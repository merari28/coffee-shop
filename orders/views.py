from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, CreateView

from .forms import OrderProductForm
from .models import Order, OrderProduct


class MyOrderView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/my_order.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        order, _ = Order.objects.get_or_create(
            is_active=True, user=self.request.user
        )
        return order


class CreateOrderProductView(LoginRequiredMixin, CreateView):
    template_name = "orders/create_order_product.html"
    form_class = OrderProductForm
    success_url = reverse_lazy("my_order")

    def form_valid(self, form):
        order, _ = Order.objects.get_or_create(
            is_active=True,
            user=self.request.user,
        )
        product = form.cleaned_data["product"]
        # If the product is already in the cart, bump the quantity instead of
        # creating a duplicate line.
        line, created = OrderProduct.objects.get_or_create(
            order=order, product=product, defaults={"quantity": 1}
        )
        if not created:
            line.quantity += 1
            line.save()
        messages.success(self.request, f"«{product.name}» agregado a tu pedido.")
        return redirect(self.success_url)


class CheckoutView(LoginRequiredMixin, View):
    """Confirm the active order: mark it inactive and email a confirmation."""

    def post(self, request):
        order = Order.objects.filter(is_active=True, user=request.user).first()
        if not order or not order.orderproduct_set.exists():
            messages.error(request, "Tu pedido está vacío.")
            return redirect("my_order")

        order.is_active = False
        order.save()

        lines = "\n".join(
            f"  - {l.quantity}x {l.product.name}  (${l.subtotal})"
            for l in order.orderproduct_set.all()
        )
        send_mail(
            subject=f"✅ Pedido #{order.id} confirmado — Coffee Shop",
            message=(
                f"Hola {order.user.username},\n\n"
                f"Tu pedido #{order.id} fue confirmado:\n\n"
                f"{lines}\n\n"
                f"Total: ${order.total}\n\n"
                "Te avisaremos cuando esté listo en la barra. ¡Gracias!\n"
                "Coffee Shop"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email] if order.user.email else [],
            fail_silently=True,
        )
        messages.success(request, f"¡Pedido #{order.id} confirmado!")
        return redirect("order_confirmation", pk=order.id)


class OrderConfirmationView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_confirmation.html"
    context_object_name = "order"

    def get_queryset(self):
        # Users can only see their own orders.
        return Order.objects.filter(user=self.request.user)
