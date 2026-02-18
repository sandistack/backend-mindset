"""
Shopping Cart models.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.products.models import ProductVariant
from apps.orders.models import Discount
from decimal import Decimal


class Cart(models.Model):
    """
    Shopping cart model.
    Supports both logged-in users (user field) and guests (session_key field).
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(max_length=255, null=True, blank=True)
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carts'
        # Either user or session_key must be set (enforced in clean())
    
    def __str__(self):
        if self.user:
            return f"Cart of {self.user.email}"
        return f"Cart {self.session_key}"
    
    def clean(self):
        """Validate that either user or session_key is set."""
        if not self.user and not self.session_key:
            raise ValidationError("Cart must have either user or session_key")
    
    @property
    def items_count(self):
        """Total number of items (sum of quantities)."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Sum of all item subtotals."""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def discount_amount(self):
        """Calculate discount amount based on applied discount."""
        if not self.discount:
            return Decimal('0.00')
        return self.discount.calculate_discount(self.subtotal)
    
    @property
    def total(self):
        """Final total after discount."""
        return self.subtotal - self.discount_amount
    
    def clear(self):
        """Remove all items from cart."""
        self.items.all().delete()
        self.discount = None
        self.save()


class CartItem(models.Model):
    """
    Individual item in shopping cart.
    """
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'variant']
        ordering = ['added_at']
    
    def __str__(self):
        return f"{self.variant.product.name} ({self.variant.name}) x{self.quantity}"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this item."""
        return self.variant.price * self.quantity
    
    @property
    def is_available(self):
        """Check if item is available in stock."""
        return (
            self.variant.is_active and
            self.variant.product.is_active and
            self.variant.is_in_stock() and
            self.variant.stock >= self.quantity
        )
    
    def clean(self):
        """Validate stock availability."""
        if self.quantity > self.variant.stock:
            raise ValidationError(
                f"Requested quantity ({self.quantity}) exceeds available stock ({self.variant.stock})"
            )
