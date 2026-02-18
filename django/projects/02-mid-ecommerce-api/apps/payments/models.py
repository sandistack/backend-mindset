from django.db import models
from django.utils import timezone
from apps.orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
    ]
    
    PROVIDER_CHOICES = [
        ('midtrans', 'Midtrans'),
        ('stripe', 'Stripe'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_transaction_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    method = models.CharField(max_length=50, blank=True)  # credit_card, bank_transfer, gopay, etc.
    
    # URLs
    payment_url = models.URLField(blank=True)
    
    # Metadata
    raw_response = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.order.order_number} ({self.status})"
    
    @property
    def is_expired(self):
        """Check if payment is expired"""
        if self.expired_at and self.status == 'pending':
            return timezone.now() > self.expired_at
        return False
