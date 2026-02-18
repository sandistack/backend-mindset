from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'provider', 'amount', 'status', 'method', 'created_at', 'paid_at']
    list_filter = ['status', 'provider', 'method', 'created_at']
    search_fields = ['order__order_number', 'provider_transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'raw_response']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'amount')
        }),
        ('Payment Details', {
            'fields': ('provider', 'provider_transaction_id', 'status', 'method')
        }),
        ('URLs', {
            'fields': ('payment_url',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'expired_at')
        }),
        ('Metadata', {
            'fields': ('raw_response',),
            'classes': ('collapse',)
        })
    )
