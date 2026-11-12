from decimal import Decimal
from django.conf import settings
from django.db import models
from store.models import Product


class Cart(models.Model):
    """
    Persistent shopping cart for an authenticated user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total_price(self) -> Decimal:
        """Calculates total monetary value of all items in the cart."""
        total = sum(item.get_cost() for item in self.items.select_related('product'))
        return Decimal(total)

    def get_total_items(self) -> int:
        """Calculates total quantity of all items in the cart."""
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Removes all items from the cart."""
        self.items.all().delete()


class CartItem(models.Model):
    """
    Represents an item within a shopping cart.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product'
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Cart #{self.cart_id})"

    def get_cost(self) -> Decimal:
        """Calculates cost of this cart line item."""
        return self.product.price * self.quantity
