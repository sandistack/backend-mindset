"""
Order views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError

from .models import Order
from .serializers import (
    CheckoutSerializer,
    OrderListSerializer,
    OrderDetailSerializer
)
from .services import OrderService
from apps.cart.services import CartService


class CheckoutView(APIView):
    """Checkout endpoint to create order from cart."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create order from cart."""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart_service = CartService(request)
        
        # Merge validated shipping data
        shipping_data = {**serializer.validated_data['shipping']}
        if 'notes' in serializer.validated_data:
            shipping_data['notes'] = serializer.validated_data.get('notes', '')
        
        try:
            order = OrderService.create_from_cart(
                user=request.user,
                cart=cart_service.cart,
                shipping_data=shipping_data
            )
            
            # Clear cache after checkout
            cart_service.invalidate_cache()
            
            # TODO: Trigger email notification (async)
            # from apps.notifications.tasks import send_order_confirmation
            # send_order_confirmation.delay(order.id)
            
            return Response(
                OrderDetailSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Customer order history and details."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only show user's own orders
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order."""
        order = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            OrderService.cancel_order(order, reason)
            return Response({
                'message': 'Order cancelled successfully',
                'order': OrderDetailSerializer(order).data
            })
        except ValidationError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class AdminOrderViewSet(viewsets.ModelViewSet):
    """Admin order management."""
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().prefetch_related('items').select_related('user')
    serializer_class = OrderDetailSerializer
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status."""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            OrderService.update_status(
                order,
                new_status,
                tracking_number=request.data.get('tracking_number', ''),
                reason=request.data.get('reason', '')
            )
            return Response(OrderDetailSerializer(order).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
