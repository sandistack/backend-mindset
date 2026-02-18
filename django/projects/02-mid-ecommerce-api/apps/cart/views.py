"""
Views for Shopping Cart.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError

from .services import CartService
from .models import CartItem
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    ApplyDiscountSerializer,
)


class CartView(APIView):
    """
    GET /api/cart/
    Get current cart for user or guest session.
    
    DELETE /api/cart/
    Clear all items from cart.
    
    No authentication required (works for guests via session).
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current cart."""
        service = CartService(request)
        data = service.get_cart_data()
        return Response(data)
    
    def delete(self, request):
        """Clear cart."""
        service = CartService(request)
        service.clear()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_204_NO_CONTENT)


class CartItemView(APIView):
    """
    POST /api/cart/items/
    Add item to cart.
    
    PUT /api/cart/items/{id}/
    Update item quantity.
    
    DELETE /api/cart/items/{id}/
    Remove item from cart.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Add item to cart.
        
        Body:
        {
            "variant_id": 1,
            "quantity": 2
        }
        """
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = CartService(request)
        
        try:
            item = service.add_item(
                variant_id=serializer.validated_data['variant_id'],
                quantity=serializer.validated_data['quantity']
            )
            
            return Response(
                CartItemSerializer(item).data,
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def put(self, request, item_id):
        """
        Update cart item quantity.
        
        Body:
        {
            "quantity": 3
        }
        
        If quantity is 0, item will be removed.
        """
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = CartService(request)
        
        try:
            service.update_item(
                item_id=item_id,
                quantity=serializer.validated_data['quantity']
            )
            
            # Return updated cart
            data = service.get_cart_data()
            return Response(data)
        
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, item_id):
        """Remove item from cart."""
        service = CartService(request)
        
        try:
            service.remove_item(item_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )


class ApplyDiscountView(APIView):
    """
    POST /api/cart/discount/
    Apply discount code to cart.
    
    DELETE /api/cart/discount/
    Remove discount from cart.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Apply discount code.
        
        Body:
        {
            "code": "DISCOUNT10"
        }
        """
        serializer = ApplyDiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = CartService(request)
        
        try:
            service.apply_discount(serializer.validated_data['code'])
            
            # Return updated cart with discount applied
            data = service.get_cart_data()
            return Response(data)
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request):
        """Remove discount from cart."""
        service = CartService(request)
        service.remove_discount()
        
        # Return updated cart
        data = service.get_cart_data()
        return Response(data)
