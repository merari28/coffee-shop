"""
End-to-end portfolio walkthrough for the Coffee Shop.

Drives a real Chromium browser through every screen of the app — public,
authenticated customer, and admin panel — exercising the real flows (login,
add-to-cart, checkout, confirmation) and saving one full-page, high-resolution
screenshot per screen into ./screenshots/.

Run (server must be up — see README):
    python e2e_portfolio/run_e2e.py
    python e2e_portfolio/run_e2e.py --base-url http://127.0.0.1:8020
"""
import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SHOTS = Path(__file__).parent / "screenshots"
SHOTS.mkdir(exist_ok=True)

VIEWPORT = {"width": 1440, "height": 900}
SCALE = 2  # device_scale_factor -> retina-quality screenshots

CUSTOMER = ("cliente", "cliente1234")
ADMIN = ("admin", "admin1234")

_counter = {"n": 0}


def shot(page, name):
    """Save a numbered, full-page screenshot."""
    _counter["n"] += 1
    page.wait_for_load_state("load")
    page.wait_for_timeout(900)  # let fonts/images settle
    path = SHOTS / f"{_counter['n']:02d}_{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  [shot] {path.name}")
    return path


def login(page, base, username, password):
    page.goto(f"{base}/usuarios/login/")
    page.fill("#id_username", username)
    page.fill("#id_password", password)
    page.click("button[type=submit]")
    page.wait_for_load_state("load")


def run(base):
    with sync_playwright() as p:
        browser = p.chromium.launch()

        def new_ctx():
            ctx = browser.new_context(
                viewport=VIEWPORT, device_scale_factor=SCALE, locale="es-ES"
            )
            return ctx, ctx.new_page()

        # ---------------- PUBLIC -------------------------------------------
        print("Public screens…")
        ctx, page = new_ctx()
        page.goto(f"{base}/productos/")
        shot(page, "menu_publico")
        page.goto(f"{base}/usuarios/registro/")
        shot(page, "registro")
        page.goto(f"{base}/usuarios/login/")
        shot(page, "login")
        ctx.close()

        # ---------------- CUSTOMER -----------------------------------------
        print("Customer flow…")
        ctx, page = new_ctx()
        login(page, base, *CUSTOMER)

        page.goto(f"{base}/productos/")
        shot(page, "menu_autenticado")

        page.goto(f"{base}/pedidos/mi-orden/")
        shot(page, "mi_pedido")

        # Add a product to the cart from the menu (real flow → redirects to cart)
        page.goto(f"{base}/productos/")
        # click the "Agregar al pedido" button inside the Espresso card
        card = page.locator("li:has(h3:text-is('Espresso'))").first
        card.scroll_into_view_if_needed()
        card.get_by_role("button", name="Agregar al pedido").click()
        page.wait_for_url("**/mi-orden/")
        shot(page, "producto_agregado")

        # Checkout → confirmation
        page.click("form[action$='checkout/'] button[type=submit]")
        page.wait_for_url("**/confirmacion/**")
        shot(page, "pedido_confirmado")
        ctx.close()

        # ---------------- ADMIN --------------------------------------------
        print("Admin panel…")
        ctx, page = new_ctx()
        page.goto(f"{base}/admin/login/")
        page.fill("#id_username", ADMIN[0])
        page.fill("#id_password", ADMIN[1])
        page.click("input[type=submit]")
        page.wait_for_load_state("load")
        shot(page, "admin_dashboard")

        page.goto(f"{base}/admin/products/product/")
        shot(page, "admin_productos")

        # Open the first product change form
        page.locator("#result_list tbody tr th a").first.click()
        page.wait_for_load_state("load")
        shot(page, "admin_producto_detalle")

        page.goto(f"{base}/admin/orders/order/")
        shot(page, "admin_pedidos")

        page.goto(f"{base}/admin/auth/user/")
        shot(page, "admin_usuarios")
        ctx.close()

        # ---------------- API ----------------------------------------------
        print("REST API…")
        ctx, page = new_ctx()
        page.goto(f"{base}/productos/api/")
        shot(page, "api_productos_json")
        ctx.close()

        browser.close()
    print(f"\nDone — {_counter['n']} screenshots in {SHOTS}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8020")
    args = ap.parse_args()
    try:
        run(args.base_url.rstrip("/"))
    except Exception as exc:  # noqa: BLE001
        print(f"E2E run failed: {exc}", file=sys.stderr)
        sys.exit(1)
