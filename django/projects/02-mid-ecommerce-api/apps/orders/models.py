"""
Orders and Discount models.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import random
import string


class Discount(models.Model):
    """
    Discount/Coupon code model.
    Can be percentage or fixed amount.
    """
    
    TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    min_order_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Minimum order amount to apply this discount"
    )
    max_discount_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum discount amount (for percentage type)"
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Total number of times this code can be used"
    )
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'discounts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} ({self.get_type_display()})"
    
    def save(self, *args, **kwargs):
        """Convert code to uppercase."""
        self.code = self.code.upper()
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """
        Check if discount is valid (active, within date range, usage limit).
        """
        now = timezone.now()
        
        # Check if active
        if not self.is_active:
            return False
        
        # Check date range
        if now < self.valid_from or now > self.valid_until:
            return False
        
        # Check usage limit
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        
        return True
    
    def calculate_discount(self, subtotal):
        """
        Calculate discount amount based on subtotal.
        Returns the discount amount.
        """
        if not self.is_valid():
            return Decimal('0.00')
        
        # Check minimum order amount
        if self.min_order_amount and subtotal < self.min_order_amount:
            return Decimal('0.00')
        
        if self.type == 'percentage':
            # Calculate percentage discount
            discount = subtotal * (self.value / Decimal('100'))
            
            # Apply max discount limit if set
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
            
            return discount
        
        else:  # fixed
            # Fixed amount discount (cannot exceed subtotal)
            return min(self.value, subtotal)
    
    def increment_usage(self):
        """Increment usage count."""
        self.used_count += 1
        self.save(update_fields=['used_count'])


class Order(models.Model):
    """
    Order model with status management.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Shipping info
    shipping_name = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    
    # Additional info
    notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number: ORD-YYYYMMDD-XXXX."""
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        order_number = f"ORD-{date_str}-{random_str}"
        
        # Ensure uniqueness
        while Order.objects.filter(order_number=order_number).exists():
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            order_number = f"ORD-{date_str}-{random_str}"
        
        return order_number
    
    def mark_paid(self):
        """Mark order as paid."""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated_at'])
    
    def mark_shipped(self, tracking_number=''):
        """Mark order as shipped."""
        self.status = 'shipped'
        self.shipped_at = timezone.now()
        if tracking_number:
            self.tracking_number = tracking_number
        self.save(update_fields=['status', 'shipped_at', 'tracking_number', 'updated_at'])
    
    def mark_completed(self):
        """Mark order as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    def cancel(self, reason=''):
        """Cancel order."""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        if reason:
            self.notes = f"{self.notes}\n\nCancelled: {reason}".strip()
        self.save(update_fields=['status', 'cancelled_at', 'notes', 'updated_at'])
    
    def can_cancel(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'paid', 'processing']


class OrderItem(models.Model):
    """
    Order item with snapshot data.
    """
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.PROTECT)
    
    # Snapshot data (in case product changes)
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        db_table = 'order_items'
        indexes = [
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.product_name} - {self.variant_name} x{self.quantity}"
