from django.urls import path
from .views import (
    CreatePaymentView,
    PaymentStatusView,
    PaymentDetailView,
    MidtransWebhookView,
    StripeWebhookView
)

app_name = 'payments'

urlpatterns = [
    # Payment creation and status
    path('orders/<int:order_id>/pay/', CreatePaymentView.as_view(), name='create-payment'),
    path('orders/<int:order_id>/payment-status/', PaymentStatusView.as_view(), name='payment-status'),
    path('payments/<int:payment_id>/', PaymentDetailView.as_view(), name='payment-detail'),
    
    # Webhooks
    path('webhooks/midtrans/', MidtransWebhookView.as_view(), name='midtrans-webhook'),
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
