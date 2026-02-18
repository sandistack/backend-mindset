"""
Orders and Discount models.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


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
