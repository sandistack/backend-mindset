# 🛒 Step 3: Shopping Cart

**Waktu:** 4-6 jam  
**Prerequisite:** Step 2 selesai

---

## 🎯 Tujuan

- Cart model untuk logged-in users
- Session-based cart untuk guests
- Cart operations (add, update, remove)
- Apply discount codes
- Cart caching dengan Redis

---

## 📋 Tasks

### 3.1 Cart Models

**Di `apps/cart/models.py`:**

```
Cart:
- id (auto)
- user (ForeignKey, null=True) - untuk logged-in users
- session_key (CharField, null=True) - untuk guests
- discount (ForeignKey to Discount, null=True)
- created_at
- updated_at

Constraints:
- Harus punya user ATAU session_key (tidak keduanya kosong)

Properties:
- items_count: Total items
- subtotal: Sum of item subtotals
- discount_amount: Calculated discount
- total: subtotal - discount_amount

Methods:
- add_item(variant, quantity)
- update_item(item_id, quantity)
- remove_item(item_id)
- clear()
- merge_guest_cart(guest_cart): Merge saat login
- apply_discount(code)
- remove_discount()
```

```
CartItem:
- id (auto)
- cart (ForeignKey to Cart)
- variant (ForeignKey to ProductVariant)
- quantity (PositiveIntegerField)
- added_at (DateTimeField, auto_now_add)

Constraints:
- unique_together = ['cart', 'variant']

Properties:
- subtotal: variant.price * quantity
- is_available: variant.is_in_stock() and variant.stock >= quantity
```

### 3.2 Discount Model

**Di `apps/orders/models.py`:**

```
Discount:
- id (auto)
- code (CharField, unique, uppercase)
- type (CharField, choices=['percentage', 'fixed'])
- value (DecimalField) - percentage (0-100) or fixed amount
- min_order_amount (DecimalField, null=True)
- max_discount_amount (DecimalField, null=True) - untuk percentage
- valid_from (DateTimeField)
- valid_until (DateTimeField)
- usage_limit (PositiveIntegerField, null=True)
- used_count (PositiveIntegerField, default=0)
- is_active (BooleanField, default=True)

Methods:
- is_valid(): Check date, usage, active
- calculate_discount(subtotal): Return discount amount
- increment_usage()
```

---

### 3.3 Cart Service

**Buat `apps/cart/services.py`:**

```python
class CartService:
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        self.session_key = request.session.session_key
        self._cart = None
    
    @property
    def cart(self):
        """Get or create cart"""
        if self._cart is None:
            if self.user:
                self._cart, _ = Cart.objects.get_or_create(user=self.user)
            else:
                if not self.session_key:
                    self.request.session.create()
                    self.session_key = self.request.session.session_key
                self._cart, _ = Cart.objects.get_or_create(session_key=self.session_key)
        return self._cart
    
    def add_item(self, variant_id, quantity=1):
        """Add item to cart"""
        variant = ProductVariant.objects.get(pk=variant_id)
        
        # Check stock
        if not variant.is_in_stock() or variant.stock < quantity:
            raise ValidationError("Insufficient stock")
        
        # Add or update
        item, created = CartItem.objects.get_or_create(
            cart=self.cart,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            item.quantity += quantity
            if item.quantity > variant.stock:
                raise ValidationError("Quantity exceeds available stock")
            item.save()
        
        self.invalidate_cache()
        return item
    
    def update_item(self, item_id, quantity):
        """Update item quantity"""
        item = CartItem.objects.get(pk=item_id, cart=self.cart)
        
        if quantity <= 0:
            item.delete()
        else:
            if quantity > item.variant.stock:
                raise ValidationError("Quantity exceeds available stock")
            item.quantity = quantity
            item.save()
        
        self.invalidate_cache()
    
    def remove_item(self, item_id):
        """Remove item from cart"""
        CartItem.objects.filter(pk=item_id, cart=self.cart).delete()
        self.invalidate_cache()
    
    def apply_discount(self, code):
        """Apply discount code"""
        try:
            discount = Discount.objects.get(code=code.upper())
        except Discount.DoesNotExist:
            raise ValidationError("Invalid discount code")
        
        if not discount.is_valid():
            raise ValidationError("Discount code is expired or invalid")
        
        if discount.min_order_amount and self.cart.subtotal < discount.min_order_amount:
            raise ValidationError(f"Minimum order amount is {discount.min_order_amount}")
        
        self.cart.discount = discount
        self.cart.save()
        self.invalidate_cache()
    
    def remove_discount(self):
        """Remove discount from cart"""
        self.cart.discount = None
        self.cart.save()
        self.invalidate_cache()
    
    def clear(self):
        """Clear all items from cart"""
        self.cart.items.all().delete()
        self.cart.discount = None
        self.cart.save()
        self.invalidate_cache()
    
    def merge_guest_cart(self):
        """Merge guest cart when user logs in"""
        if not self.user or not self.session_key:
            return
        
        try:
            guest_cart = Cart.objects.get(session_key=self.session_key)
            user_cart = self.cart
            
            for item in guest_cart.items.all():
                existing = user_cart.items.filter(variant=item.variant).first()
                if existing:
                    existing.quantity += item.quantity
                    existing.save()
                else:
                    item.cart = user_cart
                    item.save()
            
            guest_cart.delete()
        except Cart.DoesNotExist:
            pass
    
    # Redis caching
    def get_cache_key(self):
        return f"cart:{self.cart.id}"
    
    def invalidate_cache(self):
        cache.delete(self.get_cache_key())
    
    def get_cart_data(self):
        """Get cart data with caching"""
        cache_key = self.get_cache_key()
        data = cache.get(cache_key)
        
        if data is None:
            data = CartSerializer(self.cart).data
            cache.set(cache_key, data, 300)  # 5 minutes
        
        return data
```

**Referensi:** [CACHING.md](../../../docs/04-advanced/CACHING.md)

---

### 3.4 Serializers

```python
class CartItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'quantity', 'subtotal', 'is_available']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_code = serializers.CharField(source='discount.code', read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal', 'discount_code', 'discount_amount', 'total']


class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class ApplyDiscountSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
```

---

### 3.5 Views

```python
class CartView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current cart"""
        service = CartService(request)
        return Response(service.get_cart_data())


class CartItemView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = CartService(request)
        try:
            item = service.add_item(
                serializer.validated_data['variant_id'],
                serializer.validated_data['quantity']
            )
            return Response(CartItemSerializer(item).data, status=201)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
    
    def put(self, request, item_id):
        """Update item quantity"""
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = CartService(request)
        try:
            service.update_item(item_id, serializer.validated_data['quantity'])
            return Response(service.get_cart_data())
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
    
    def delete(self, request, item_id):
        """Remove item from cart"""
        service = CartService(request)
        service.remove_item(item_id)
        return Response(status=204)


class ApplyDiscountView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Apply discount code"""
        serializer = ApplyDiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = CartService(request)
        try:
            service.apply_discount(serializer.validated_data['code'])
            return Response(service.get_cart_data())
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
    
    def delete(self, request):
        """Remove discount"""
        service = CartService(request)
        service.remove_discount()
        return Response(service.get_cart_data())
```

---

## 🗂️ API Endpoints

```
GET    /api/cart/                   # Get cart
POST   /api/cart/items/             # Add item
PUT    /api/cart/items/{id}/        # Update quantity
DELETE /api/cart/items/{id}/        # Remove item
POST   /api/cart/discount/          # Apply discount
DELETE /api/cart/discount/          # Remove discount
DELETE /api/cart/                   # Clear cart
```

---

## ✅ Checklist

- [ ] Cart model (user + session support)
- [ ] CartItem model
- [ ] Discount model dengan validation
- [ ] CartService dengan semua methods
- [ ] Redis caching untuk cart data
- [ ] Add/update/remove items
- [ ] Apply/remove discount
- [ ] Merge guest cart on login
- [ ] Stock validation
- [ ] API endpoints

---

## 🔗 Referensi

- [CACHING.md](../../../docs/04-advanced/CACHING.md) - Redis caching patterns

---

## ➡️ Next Step

Lanjut ke [04-ORDER_MANAGEMENT.md](04-ORDER_MANAGEMENT.md) - Order Processing
