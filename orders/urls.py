from .views import MyOrderView, CreateOrderProductView
from django.urls import path

urlpatterns = [
    path('mi-orden/', MyOrderView.as_view(), name="my_order"),
    path('agregar-producto/', CreateOrderProductView.as_view(), name="add_product")
]
