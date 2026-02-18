from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.orders.models import Order
from .models import Payment
from .services import PaymentService, StripeService
from .serializers import (
    PaymentSerializer,
    CreatePaymentSerializer,
    PaymentStatusSerializer
)


class CreatePaymentView(APIView):
    """
    Create payment for an order
    
    POST /api/orders/{order_id}/pay/
    Body: {"provider": "midtrans" or "stripe"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        """Create payment for order"""
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        
        # Validate order status
        if order.status != 'pending':
            return Response(
                {'error': 'Order is not pending payment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get provider from request
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data['provider']
        
        try:
            service = PaymentService(provider=provider)
            payment = service.create_payment(order)
            
            return Response({
                'payment_id': payment.id,
                'provider': payment.provider,
                'payment_url': payment.payment_url,
                'amount': str(payment.amount),
                'expires_at': payment.expired_at,
                'status': payment.status
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create payment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentStatusView(APIView):
    """
    Get payment status for an order
    
    GET /api/orders/{order_id}/payment-status/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        """Check payment status"""
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        
        if not hasattr(order, 'payment'):
            return Response(
                {'error': 'No payment found for this order'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        payment = order.payment
        provider = payment.provider
        
        # Get fresh status from payment service
        service = PaymentService(provider=provider)
        payment_status = service.get_payment_status(order)
        
        serializer = PaymentStatusSerializer(payment_status)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class MidtransWebhookView(APIView):
    """
    Handle Midtrans webhook notifications
    
    POST /api/webhooks/midtrans/
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        """Handle payment webhook from Midtrans"""
        try:
            service = PaymentService(provider='midtrans')
            payment = service.handle_notification(request.data)
            
            return Response({
                'status': 'ok',
                'payment_id': payment.id,
                'payment_status': payment.status
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Log error but return 200 to prevent retries
            print(f"Midtrans webhook error: {e}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_200_OK
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Handle Stripe webhook notifications
    
    POST /api/webhooks/stripe/
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        """Handle payment webhook from Stripe"""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            # Verify signature and get event
            stripe_service = StripeService()
            event = stripe_service.verify_webhook_signature(payload, sig_header)
            
            # Handle notification
            service = PaymentService(provider='stripe')
            payment = service.handle_notification(event)
            
            if payment:
                return Response({
                    'status': 'ok',
                    'payment_id': payment.id,
                    'payment_status': payment.status
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'ok',
                    'message': 'Event processed'
                }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Log error but return 200 to prevent retries
            print(f"Stripe webhook error: {e}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_200_OK
            )


class PaymentDetailView(APIView):
    """
    Get payment details
    
    GET /api/payments/{payment_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        """Get payment details"""
        payment = get_object_or_404(
            Payment.objects.select_related('order'),
            pk=payment_id,
            order__user=request.user
        )
        
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

