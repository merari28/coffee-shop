from django.db import models
from django.contrib.auth.models import User

from products.models import Product


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user}"

    @property
    def total(self):
        """Sum of price * quantity across every line in the order."""
        return sum(
            (line.product.price * line.quantity for line in self.orderproduct_set.all()),
            0,
        )

    @property
    def item_count(self):
        return sum(line.quantity for line in self.orderproduct_set.all())


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.order} - {self.product}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity
