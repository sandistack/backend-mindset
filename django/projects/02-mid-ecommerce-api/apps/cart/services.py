"""
Cart business logic service.
"""

from django.core.cache import cache
from django.core.exceptions import ValidationError
from .models import Cart, CartItem
from apps.products.models import ProductVariant
from apps.orders.models import Discount


class CartService:
    """
    Service class to handle cart operations:
    - Get/create cart for user or guest
    - Add/update/remove items
    - Apply/remove discount
    - Merge guest cart when user logs in
    - Cache cart data with Redis
    """
    
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        self.session_key = request.session.session_key
        self._cart = None
    
    @property
    def cart(self):
        """
        Get or create cart for current user/session.
        Lazy loading - only created when accessed.
        """
        if self._cart is None:
            if self.user:
                # Logged-in user
                self._cart, created = Cart.objects.get_or_create(user=self.user)
            else:
                # Guest user
                if not self.session_key:
                    # Create session if not exists
                    self.request.session.create()
                    self.session_key = self.request.session.session_key
                
                self._cart, created = Cart.objects.get_or_create(
                    session_key=self.session_key
                )
        
        return self._cart
    
    def add_item(self, variant_id, quantity=1):
        """
        Add item to cart or update quantity if already exists.
        
        Args:
            variant_id: ProductVariant ID
            quantity: Quantity to add
        
        Returns:
            CartItem instance
        
        Raises:
            ValidationError: If stock insufficient
        """
        try:
            variant = ProductVariant.objects.select_related('product').get(
                pk=variant_id,
                is_active=True,
                product__is_active=True
            )
        except ProductVariant.DoesNotExist:
            raise ValidationError("Product variant not found or inactive")
        
        # Check stock availability
        if not variant.is_in_stock():
            raise ValidationError("Product is out of stock")
        
        if variant.stock < quantity:
            raise ValidationError(
                f"Insufficient stock. Available: {variant.stock}, Requested: {quantity}"
            )
        
        # Get or create cart item
        item, created = CartItem.objects.get_or_create(
            cart=self.cart,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Item already in cart, increase quantity
            new_quantity = item.quantity + quantity
            
            # Check stock for new quantity
            if new_quantity > variant.stock:
                raise ValidationError(
                    f"Total quantity ({new_quantity}) exceeds available stock ({variant.stock})"
                )
            
            item.quantity = new_quantity
            item.save()
        
        # Invalidate cache
        self.invalidate_cache()
        
        return item
    
    def update_item(self, item_id, quantity):
        """
        Update cart item quantity.
        If quantity is 0, remove the item.
        
        Args:
            item_id: CartItem ID
            quantity: New quantity
        
        Raises:
            CartItem.DoesNotExist: If item not found in cart
            ValidationError: If stock insufficient
        """
        item = CartItem.objects.select_related('variant').get(
            pk=item_id,
            cart=self.cart
        )
        
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            item.delete()
        else:
            # Check stock
            if quantity > item.variant.stock:
                raise ValidationError(
                    f"Quantity ({quantity}) exceeds available stock ({item.variant.stock})"
                )
            
            item.quantity = quantity
            item.save()
        
        self.invalidate_cache()
    
    def remove_item(self, item_id):
        """
        Remove item from cart.
        
        Args:
            item_id: CartItem ID
        """
        CartItem.objects.filter(pk=item_id, cart=self.cart).delete()
        self.invalidate_cache()
    
    def apply_discount(self, code):
        """
        Apply discount code to cart.
        
        Args:
            code: Discount code
        
        Raises:
            ValidationError: If code invalid, expired, or minimum not met
        """
        try:
            discount = Discount.objects.get(code=code.upper())
        except Discount.DoesNotExist:
            raise ValidationError("Invalid discount code")
        
        # Check if discount is valid
        if not discount.is_valid():
            raise ValidationError("Discount code is expired or usage limit reached")
        
        # Check minimum order amount
        if discount.min_order_amount and self.cart.subtotal < discount.min_order_amount:
            raise ValidationError(
                f"Minimum order amount is ${discount.min_order_amount}"
            )
        
        # Apply discount
        self.cart.discount = discount
        self.cart.save()
        self.invalidate_cache()
    
    def remove_discount(self):
        """Remove discount from cart."""
        self.cart.discount = None
        self.cart.save()
        self.invalidate_cache()
    
    def clear(self):
        """Clear all items and discount from cart."""
        self.cart.clear()
        self.invalidate_cache()
    
    def merge_guest_cart(self):
        """
        Merge guest cart into user cart when user logs in.
        Called after successful login.
        """
        if not self.user or not self.session_key:
            return
        
        try:
            # Get guest cart
            guest_cart = Cart.objects.get(session_key=self.session_key)
            
            # Get or create user cart
            user_cart, _ = Cart.objects.get_or_create(user=self.user)
            
            # Merge items
            for guest_item in guest_cart.items.all():
                # Check if item already in user cart
                user_item = user_cart.items.filter(variant=guest_item.variant).first()
                
                if user_item:
                    # Increase quantity
                    user_item.quantity += guest_item.quantity
                    user_item.save()
                else:
                    # Move item to user cart
                    guest_item.cart = user_cart
                    guest_item.save()
            
            # Delete guest cart
            guest_cart.delete()
            
            # Update current cart reference
            self._cart = user_cart
            self.invalidate_cache()
            
        except Cart.DoesNotExist:
            # No guest cart to merge
            pass
    
    # ============================================
    # REDIS CACHING
    # ============================================
    
    def get_cache_key(self):
        """Generate cache key for cart."""
        return f"cart:{self.cart.id}"
    
    def invalidate_cache(self):
        """Invalidate cart cache."""
        cache.delete(self.get_cache_key())
    
    def get_cart_data(self):
        """
        Get cart data with caching.
        Cache for 5 minutes to reduce database queries.
        
        Returns:
            dict: Serialized cart data
        """
        from .serializers import CartSerializer
        
        cache_key = self.get_cache_key()
        data = cache.get(cache_key)
        
        if data is None:
            # Cache miss, fetch from database
            cart = Cart.objects.prefetch_related(
                'items__variant__product',
                'items__variant__product__category',
                'discount'
            ).get(pk=self.cart.id)
            
            data = CartSerializer(cart, context={'request': self.request}).data
            
            # Cache for 5 minutes (300 seconds)
            cache.set(cache_key, data, 300)
        
        return data
