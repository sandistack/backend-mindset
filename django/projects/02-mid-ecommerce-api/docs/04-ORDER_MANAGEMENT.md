# 📦 Step 4: Order Management

**Waktu:** 6-8 jam  
**Prerequisite:** Step 3 selesai

---

## 🎯 Tujuan

- Order & OrderItem models
- Checkout process dari cart
- Order status management
- Order history

---

## 📋 Tasks

### 4.1 Order Models

**Di `apps/orders/models.py`:**

```
Order:
- id (auto)
- user (ForeignKey to User)
- order_number (CharField, unique) - e.g., "ORD-20240315-XXXX"
- status (CharField, choices - lihat di bawah)
- subtotal (DecimalField)
- discount_amount (DecimalField, default=0)
- shipping_cost (DecimalField, default=0)
- total (DecimalField)
- discount (ForeignKey to Discount, null=True)
- notes (TextField, blank=True)

# Shipping info
- shipping_name (CharField)
- shipping_phone (CharField)
- shipping_address (TextField)
- shipping_city (CharField)
- shipping_postal_code (CharField)

# Timestamps
- created_at
- updated_at
- paid_at (DateTimeField, null=True)
- shipped_at (DateTimeField, null=True)
- completed_at (DateTimeField, null=True)
- cancelled_at (DateTimeField, null=True)

Order Status Choices:
- pending: Menunggu pembayaran
- paid: Sudah dibayar
- processing: Sedang diproses
- shipped: Sudah dikirim
- delivered: Sudah diterima
- completed: Selesai
- cancelled: Dibatalkan

Methods:
- generate_order_number(): Static method
- mark_paid()
- mark_shipped(tracking_number)
- mark_completed()
- cancel(reason)
- can_cancel(): Boolean
```

```
OrderItem:
- id (auto)
- order (ForeignKey to Order)
- variant (ForeignKey to ProductVariant)
- product_name (CharField) - snapshot, karena product bisa berubah
- variant_name (CharField) - snapshot
- price (DecimalField) - snapshot harga saat order
- quantity (PositiveIntegerField)
- subtotal (DecimalField)
```

### 4.2 Order Service

**Buat `apps/orders/services.py`:**

```python
class OrderService:
    
    @staticmethod
    def create_from_cart(user, cart, shipping_data):
        """Create order from cart"""
        
        # Validate cart not empty
        if not cart.items.exists():
            raise ValidationError("Cart is empty")
        
        # Validate all items available
        for item in cart.items.all():
            if not item.is_available:
                raise ValidationError(f"{item.variant.name} is not available")
        
        # Create order
        order = Order.objects.create(
            user=user,
            order_number=Order.generate_order_number(),
            subtotal=cart.subtotal,
            discount=cart.discount,
            discount_amount=cart.discount_amount,
            shipping_cost=shipping_data.get('shipping_cost', 0),
            total=cart.total + shipping_data.get('shipping_cost', 0),
            shipping_name=shipping_data['name'],
            shipping_phone=shipping_data['phone'],
            shipping_address=shipping_data['address'],
            shipping_city=shipping_data['city'],
            shipping_postal_code=shipping_data['postal_code'],
        )
        
        # Create order items & reserve stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                product_name=item.variant.product.name,
                variant_name=item.variant.name,
                price=item.variant.price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            
            # Reserve stock
            item.variant.reserve_stock(item.quantity)
        
        # Increment discount usage
        if cart.discount:
            cart.discount.increment_usage()
        
        # Clear cart
        cart.items.all().delete()
        cart.discount = None
        cart.save()
        
        return order
    
    @staticmethod
    def cancel_order(order, reason=""):
        """Cancel order and release stock"""
        if not order.can_cancel():
            raise ValidationError("Order cannot be cancelled")
        
        # Release stock
        for item in order.items.all():
            item.variant.release_stock(item.quantity)
        
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.notes = f"Cancelled: {reason}"
        order.save()
        
        return order
    
    @staticmethod
    def update_status(order, new_status, **kwargs):
        """Update order status"""
        valid_transitions = {
            'pending': ['paid', 'cancelled'],
            'paid': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': ['completed'],
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            raise ValidationError(f"Cannot transition from {order.status} to {new_status}")
        
        order.status = new_status
        
        if new_status == 'paid':
            order.paid_at = timezone.now()
        elif new_status == 'shipped':
            order.shipped_at = timezone.now()
            order.tracking_number = kwargs.get('tracking_number')
        elif new_status == 'completed':
            order.completed_at = timezone.now()
        
        order.save()
        return order
```

---

### 4.3 Serializers

```python
class ShippingDataSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=10)
    shipping_cost = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)


class CheckoutSerializer(serializers.Serializer):
    shipping = ShippingDataSerializer()
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'variant_name', 'price', 'quantity', 'subtotal']


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'total', 'items_count', 'created_at']
    
    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'items',
            'subtotal', 'discount_amount', 'shipping_cost', 'total',
            'shipping_name', 'shipping_phone', 'shipping_address',
            'shipping_city', 'shipping_postal_code',
            'notes', 'created_at', 'paid_at', 'shipped_at'
        ]
```

---

### 4.4 Views

```python
class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create order from cart"""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart_service = CartService(request)
        
        try:
            order = OrderService.create_from_cart(
                user=request.user,
                cart=cart_service.cart,
                shipping_data=serializer.validated_data['shipping']
            )
            
            # Trigger email notification (async)
            # send_order_confirmation.delay(order.id)
            
            return Response(
                OrderDetailSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order"""
        order = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            OrderService.cancel_order(order, reason)
            return Response({'message': 'Order cancelled'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)


# Admin views for status updates
class AdminOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        try:
            OrderService.update_status(
                order,
                new_status,
                tracking_number=request.data.get('tracking_number')
            )
            return Response(OrderDetailSerializer(order).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
```

---

## 🗂️ API Endpoints

```
# Customer
POST   /api/orders/                     # Checkout (create order)
GET    /api/orders/                     # Order history
GET    /api/orders/{id}/                # Order detail
POST   /api/orders/{id}/cancel/         # Cancel order

# Admin
GET    /api/admin/orders/               # All orders
GET    /api/admin/orders/{id}/          # Order detail
POST   /api/admin/orders/{id}/update-status/  # Update status
```

---

## ✅ Checklist

- [ ] Order model dengan semua fields
- [ ] OrderItem model dengan snapshots
- [ ] Order number generation
- [ ] OrderService dengan checkout logic
- [ ] Stock reservation on checkout
- [ ] Stock release on cancel
- [ ] Status transitions validation
- [ ] Discount usage increment
- [ ] Cart clearing after checkout
- [ ] Customer order history
- [ ] Admin order management
- [ ] Cancel functionality

---

## 🔗 Referensi

- [SIGNALS.md](../../../docs/04-advanced/SIGNALS.md) - Post-order signals

---

## ➡️ Next Step

Lanjut ke [05-FILE_UPLOAD.md](05-FILE_UPLOAD.md) - Product Image Upload
