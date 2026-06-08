"""
Seed the database with realistic demo data for the Coffee Shop.

Idempotent: safe to run multiple times. Creates:
  * A staff/admin user and a normal customer (known, documented credentials).
  * A catalogue of coffee products, each with a real photo.
  * A historical (confirmed) order and an active cart for the customer.
  * Profile avatars downloaded from randomuser.me.

Product photos come from the repository's bundled `logos/` images (guaranteed
coffee shots) and are topped up with extra shots from Unsplash. Every remote
download is validated as a real image with Pillow; if a download fails the
command falls back to a bundled image so the demo never ends up with a broken
<img>.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # wipe demo data first
"""
import io
import shutil
from decimal import Decimal
from pathlib import Path

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image

from products.models import Product
from orders.models import Order, OrderProduct
from users.models import Profile

# Known demo credentials (documented in the README / final summary).
ADMIN = {"username": "admin", "password": "admin1234", "email": "admin@coffeeshop.demo"}
CUSTOMER = {"username": "cliente", "password": "cliente1234", "email": "cliente@coffeeshop.demo"}

BUNDLED_LOGOS = Path(settings.BASE_DIR) / "logos"

# Each product points at a bundled image (always present) and optionally a
# higher-res Unsplash shot to use when reachable.
PRODUCTS = [
    {
        "name": "Cappuccino",
        "description": "Espresso doble con leche vaporizada y una corona de espuma sedosa.",
        "price": Decimal("3.50"),
        "bundled": "cappuccino.png",
        "unsplash": "photo-1572442388796-11668a67e53d",
    },
    {
        "name": "Latte",
        "description": "Espresso suave con abundante leche cremosa y un toque de arte latte.",
        "price": Decimal("3.80"),
        "bundled": "latte.png",
        "unsplash": "photo-1561882468-9110e03e0f78",
    },
    {
        "name": "Americano Helado",
        "description": "Espresso sobre hielo y agua fría: refrescante, intenso y sin azúcar.",
        "price": Decimal("3.20"),
        "bundled": "Ice.Americano.png",
        "unsplash": "photo-1517701550927-30cf4ba1dba5",
    },
    {
        "name": "Chocolate Caliente",
        "description": "Chocolate belga fundido con leche cremosa y malvaviscos.",
        "price": Decimal("4.00"),
        "bundled": "chocolate.png",
        "unsplash": "photo-1542990253-0d0f5be5f0ed",
    },
    {
        "name": "Café Cocido",
        "description": "Nuestro café de la casa, recién filtrado, de cuerpo redondo y notas a cacao.",
        "price": Decimal("2.80"),
        "bundled": "cocido.png",
        "unsplash": "photo-1495474472287-4d71bcdd2085",
    },
    {
        "name": "Espresso",
        "description": "Un shot corto e intenso, crema avellanada y carácter puro de café.",
        "price": Decimal("2.50"),
        "bundled": "cocido.png",
        "unsplash": "photo-1510591509098-f4fdc6d0ff04",
    },
    {
        "name": "Mocha",
        "description": "La unión perfecta de espresso, chocolate y leche cremosa coronada con cacao.",
        "price": Decimal("4.20"),
        "bundled": "chocolate.png",
        "unsplash": "photo-1570968915860-54d5c301fa9f",
    },
    {
        "name": "Cold Brew",
        "description": "Extracción en frío durante 18 horas: dulce natural, baja acidez, mucha cafeína.",
        "price": Decimal("3.90"),
        "bundled": "Ice.Americano.png",
        "unsplash": "photo-1461023058943-07fcbe16d735",
    },
]


class Command(BaseCommand):
    help = "Populate the database with realistic demo data and real images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo orders/products/profiles before seeding.",
        )

    # ---- image helpers ---------------------------------------------------
    def _validate_image(self, raw: bytes) -> bytes | None:
        """Return JPEG/PNG bytes if `raw` is a real, decodable image."""
        try:
            img = Image.open(io.BytesIO(raw))
            img.verify()
            if min(img.size) < 80:  # tiny -> almost certainly an error placeholder
                return None
            return raw
        except Exception:
            return None

    def _fetch_unsplash(self, photo_id: str) -> bytes | None:
        url = f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=900&q=80"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                return self._validate_image(r.content)
        except requests.RequestException:
            pass
        return None

    def _product_image(self, spec) -> tuple[str, bytes]:
        """(filename, bytes) for a product, preferring Unsplash, else bundled."""
        data = self._fetch_unsplash(spec["unsplash"]) if spec.get("unsplash") else None
        if data:
            return f"{spec['name'].lower().replace(' ', '_')}.jpg", data
        bundled = BUNDLED_LOGOS / spec["bundled"]
        return spec["bundled"], bundled.read_bytes()

    def _fetch_avatars(self, count: int) -> list[bytes]:
        try:
            r = requests.get(
                f"https://randomuser.me/api/?results={count}&inc=picture",
                timeout=20,
            )
            urls = [u["picture"]["large"] for u in r.json()["results"]]
            out = []
            for u in urls:
                img = requests.get(u, timeout=20)
                data = self._validate_image(img.content) if img.status_code == 200 else None
                if data:
                    out.append(data)
            return out
        except (requests.RequestException, KeyError, ValueError):
            return []

    # ---- main ------------------------------------------------------------
    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing demo data...")
            OrderProduct.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            Profile.objects.all().update(avatar="")
            User.objects.filter(
                username__in=[ADMIN["username"], CUSTOMER["username"]]
            ).delete()

        # --- users --------------------------------------------------------
        admin, created = User.objects.get_or_create(
            username=ADMIN["username"],
            defaults={"email": ADMIN["email"], "is_staff": True, "is_superuser": True},
        )
        admin.email = ADMIN["email"]
        admin.is_staff = admin.is_superuser = True
        admin.set_password(ADMIN["password"])
        admin.save()

        customer, _ = User.objects.get_or_create(
            username=CUSTOMER["username"], defaults={"email": CUSTOMER["email"]}
        )
        customer.email = CUSTOMER["email"]
        customer.set_password(CUSTOMER["password"])
        customer.save()
        self.stdout.write(self.style.SUCCESS("[OK] Users ready: admin / cliente"))

        # --- avatars ------------------------------------------------------
        avatars = self._fetch_avatars(2)
        for user, av in zip((admin, customer), avatars):
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.bio = (
                "Barista jefe ☕" if user == admin else "Cliente fiel desde 2024"
            )
            profile.avatar.save(f"{user.username}.jpg", ContentFile(av), save=True)
        if avatars:
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(avatars)} avatar(s) downloaded"))
        else:
            self.stdout.write(self.style.WARNING("! Avatars unavailable (offline) — skipped"))

        # --- products -----------------------------------------------------
        created_products = []
        for spec in PRODUCTS:
            product, _ = Product.objects.get_or_create(
                name=spec["name"],
                defaults={"description": spec["description"], "price": spec["price"]},
            )
            product.description = spec["description"]
            product.price = spec["price"]
            product.available = True
            if not product.photo:
                fname, data = self._product_image(spec)
                product.photo.save(fname, ContentFile(data), save=False)
            product.save()
            created_products.append(product)
        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_products)} products with photos"))

        # --- orders -------------------------------------------------------
        # One confirmed historical order…
        Order.objects.filter(user=customer).delete()
        history = Order.objects.create(user=customer, is_active=False)
        OrderProduct.objects.create(order=history, product=created_products[0], quantity=2)
        OrderProduct.objects.create(order=history, product=created_products[4], quantity=1)
        # …and a live cart with a couple of items.
        cart = Order.objects.create(user=customer, is_active=True)
        OrderProduct.objects.create(order=cart, product=created_products[1], quantity=1)
        OrderProduct.objects.create(order=cart, product=created_products[6], quantity=2)
        self.stdout.write(self.style.SUCCESS("[OK] Orders: 1 confirmed + 1 active cart"))

        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully."))
        self.stdout.write(f"  Admin   -> {ADMIN['username']} / {ADMIN['password']}")
        self.stdout.write(f"  Cliente -> {CUSTOMER['username']} / {CUSTOMER['password']}")
