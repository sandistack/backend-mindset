# 📦 Step 2: Product Catalog

**Waktu:** 6-8 jam  
**Prerequisite:** Step 1 selesai

---

## 🎯 Tujuan

- Membuat Category model dengan nested structure
- Product model dengan variants
- Product images
- Search & filtering

---

## 📋 Tasks

### 2.1 Category Model

**Di `apps/products/models.py`:**

Category dengan self-referential (parent-child):

```
Fields:
- id (auto)
- name (CharField, max_length=100)
- slug (SlugField, unique)
- parent (ForeignKey to self, null=True)
- description (TextField, blank=True)
- image (ImageField, optional)
- is_active (BooleanField, default=True)
- order (PositiveIntegerField, default=0)
- created_at, updated_at

Properties:
- get_ancestors(): Return list of parent categories
- get_descendants(): Return list of child categories
- get_full_path(): Return "Parent > Child > Grandchild"

Manager:
- active(): Filter is_active=True
- root_categories(): Filter parent=None
```

### 2.2 Product Model

```
Fields:
- id (auto)
- category (ForeignKey to Category)
- name (CharField, max_length=255)
- slug (SlugField, unique)
- description (TextField)
- base_price (DecimalField, max_digits=12, decimal_places=2)
- is_active (BooleanField, default=True)
- is_featured (BooleanField, default=False)
- created_at, updated_at

Properties:
- primary_image: Return first ProductImage
- price_range: Return min-max price dari variants
- total_stock: Sum stock dari semua variants
- average_rating: Dari reviews (bonus)
```

### 2.3 ProductVariant Model

```
Fields:
- id (auto)
- product (ForeignKey to Product)
- sku (CharField, unique)
- name (CharField) - e.g., "Red - Large"
- size (CharField, blank=True)
- color (CharField, blank=True)
- price (DecimalField) - bisa override base_price
- stock (PositiveIntegerField, default=0)
- weight (DecimalField, optional) - untuk shipping
- is_active (BooleanField, default=True)

Methods:
- is_in_stock(): Return stock > 0
- reserve_stock(quantity): Kurangi stock
- release_stock(quantity): Kembalikan stock
```

### 2.4 ProductImage Model

```
Fields:
- id (auto)
- product (ForeignKey to Product)
- image (ImageField) - untuk sekarang local, nanti S3
- alt_text (CharField)
- is_primary (BooleanField, default=False)
- order (PositiveIntegerField, default=0)
- created_at

Meta:
- ordering = ['order', 'created_at']
```

---

## 📝 Serializers

### CategorySerializer

```python
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    full_path = serializers.CharField(read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'children', 'full_path', 'image']
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data
```

### ProductListSerializer (untuk list view)

```python
class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'category', 'base_price', 
                  'price_range', 'primary_image', 'is_featured']
```

### ProductDetailSerializer (untuk detail view)

```python
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category',
                  'base_price', 'variants', 'images', 'is_featured']
```

---

## 🔍 Filtering

**Buat `apps/products/filters.py`:**

```python
class ProductFilter(django_filters.FilterSet):
    # Price range
    min_price = django_filters.NumberFilter(
        field_name='base_price', lookup_expr='gte'
    )
    max_price = django_filters.NumberFilter(
        field_name='base_price', lookup_expr='lte'
    )
    
    # Category (termasuk subcategories)
    category = django_filters.NumberFilter(method='filter_category')
    
    # In stock only
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    
    # Featured
    is_featured = django_filters.BooleanFilter()
    
    def filter_category(self, queryset, name, value):
        """Filter by category dan semua subcategories"""
        try:
            category = Category.objects.get(pk=value)
            descendants = category.get_descendants()
            category_ids = [category.id] + [c.id for c in descendants]
            return queryset.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            return queryset.none()
    
    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(variants__stock__gt=0).distinct()
        return queryset
```

---

## 🎯 Views

**`apps/products/views.py`:**

```python
# Public Views (AllowAny)
class CategoryListView(generics.ListAPIView):
    """List root categories with nested children"""
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(parent=None, is_active=True)


class ProductListView(generics.ListAPIView):
    """List products with filtering & search"""
    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'base_price', 'name']
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')


class ProductDetailView(generics.RetrieveAPIView):
    """Product detail with variants & images"""
    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related(
            'variants', 'images'
        )


# Admin Views (IsAdminUser)
class AdminProductViewSet(viewsets.ModelViewSet):
    """Admin CRUD untuk products"""
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return ProductListSerializer
        return ProductDetailSerializer
```

---

## 🗂️ API Endpoints

```
# Public
GET    /api/categories/                  # Category tree
GET    /api/products/                    # Product list
GET    /api/products/?category=1         # Filter by category
GET    /api/products/?min_price=100&max_price=500
GET    /api/products/?search=laptop
GET    /api/products/?in_stock=true
GET    /api/products/{slug}/             # Product detail

# Admin
GET    /api/admin/products/              # All products
POST   /api/admin/products/              # Create
PUT    /api/admin/products/{id}/         # Update
DELETE /api/admin/products/{id}/         # Delete
```

---

## ✅ Checklist

- [ ] Category model dengan nested structure
- [ ] Product model dengan properties
- [ ] ProductVariant dengan stock management
- [ ] ProductImage model
- [ ] Serializers (List vs Detail)
- [ ] Filters (price, category, in_stock)
- [ ] Search functionality
- [ ] Public endpoints (AllowAny)
- [ ] Admin endpoints (IsAdminUser)
- [ ] Tests untuk models dan API

---

## 🧪 Testing

```bash
# Create category
curl -X POST http://localhost:8000/api/admin/categories/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Electronics", "slug": "electronics"}'

# Create product
curl -X POST http://localhost:8000/api/admin/products/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 15",
    "slug": "iphone-15",
    "category": 1,
    "base_price": "15000000",
    "description": "Latest iPhone"
  }'

# List products (public)
curl http://localhost:8000/api/products/

# Filter products
curl "http://localhost:8000/api/products/?category=1&min_price=10000000"
```

---

## 🔗 Referensi

- [SERIALIZERS.md](../../../docs/02-database/SERIALIZERS.md) - Nested serializers
- [FILTERING_SEARCH.md](../../../docs/02-database/FILTERING_SEARCH.md) - Advanced filtering

---

## ➡️ Next Step

Lanjut ke [03-SHOPPING_CART.md](03-SHOPPING_CART.md) - Shopping Cart Implementation
