from .views import (
    MyOrderView,
    CreateOrderProductView,
    CheckoutView,
    OrderConfirmationView,
)
from django.urls import path

urlpatterns = [
    path('mi-orden/', MyOrderView.as_view(), name="my_order"),
    path('agregar-producto/', CreateOrderProductView.as_view(), name="add_to_order"),
    path('checkout/', CheckoutView.as_view(), name="checkout"),
    path('confirmacion/<int:pk>/', OrderConfirmationView.as_view(), name="order_confirmation"),
]
