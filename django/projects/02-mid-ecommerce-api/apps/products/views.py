"""
Views for Product catalog (Public & Admin).
"""

from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch

from .models import Category, Product, ProductVariant, ProductImage
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductVariantSerializer,
    ProductVariantCreateUpdateSerializer,
    ProductImageSerializer,
)
from .filters import ProductFilter


# ============================================
# PUBLIC VIEWS (Customer facing)
# ============================================

class CategoryListView(generics.ListAPIView):
    """
    GET /api/categories/
    List root categories with nested children.
    Public endpoint - no authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        """Return only root categories (no parent) that are active."""
        return Category.objects.filter(parent=None, is_active=True)


class ProductListView(generics.ListAPIView):
    """
    GET /api/products/
    List all active products with filtering, search, and ordering.
    
    Filter examples:
    - /api/products/?category=1
    - /api/products/?min_price=100&max_price=500
    - /api/products/?search=laptop
    - /api/products/?in_stock=true
    - /api/products/?is_featured=true
    
    Public endpoint - no authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'base_price', 'name']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """
        Return only active products with optimized queries.
        Use select_related for category (FK) and prefetch_related for variants (reverse FK).
        """
        return Product.objects.filter(is_active=True).select_related(
            'category'
        ).prefetch_related(
            'variants', 
            'images'
        )


class ProductDetailView(generics.RetrieveAPIView):
    """
    GET /api/products/{slug}/
    Get product detail with variants and images.
    Public endpoint - no authentication required.
    """
    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Return active products with related data."""
        return Product.objects.filter(is_active=True).select_related(
            'category'
        ).prefetch_related(
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True)),
            'images'
        )


# ============================================
# ADMIN VIEWS (Management)
# ============================================

class AdminProductViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for products.
    
    Endpoints:
    - GET    /api/admin/products/          # List all products
    - POST   /api/admin/products/          # Create product
    - GET    /api/admin/products/{id}/     # Product detail
    - PUT    /api/admin/products/{id}/     # Update product
    - PATCH  /api/admin/products/{id}/     # Partial update
    - DELETE /api/admin/products/{id}/     # Delete product
    
    Requires admin authentication.
    """
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all().select_related('category').prefetch_related('variants', 'images')
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'slug']
    ordering_fields = ['created_at', 'base_price', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for list vs create/update."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for categories.
    Requires admin authentication.
    """
    permission_classes = [IsAdminUser]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ['name', 'slug']
    ordering = ['order', 'name']


class AdminProductVariantViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for product variants.
    
    Endpoints:
    - GET    /api/admin/variants/          # List all variants
    - POST   /api/admin/variants/          # Create variant
    - GET    /api/admin/variants/{id}/     # Variant detail
    - PUT    /api/admin/variants/{id}/     # Update variant
    - DELETE /api/admin/variants/{id}/     # Delete variant
    
    Requires admin authentication.
    """
    permission_classes = [IsAdminUser]
    queryset = ProductVariant.objects.all().select_related('product')
    serializer_class = ProductVariantCreateUpdateSerializer
    search_fields = ['sku', 'name']
    filterset_fields = ['product', 'is_active']
    ordering = ['product', 'name']
    
    @action(detail=True, methods=['post'])
    def reserve_stock(self, request, pk=None):
        """
        POST /api/admin/variants/{id}/reserve_stock/
        Reserve stock for a variant.
        Body: {"quantity": 5}
        """
        variant = self.get_object()
        quantity = request.data.get('quantity')
        
        if not quantity or quantity <= 0:
            return Response(
                {'error': 'Valid quantity required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            variant.reserve_stock(quantity)
            return Response({
                'message': f'Reserved {quantity} units',
                'remaining_stock': variant.stock
            })
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def release_stock(self, request, pk=None):
        """
        POST /api/admin/variants/{id}/release_stock/
        Release reserved stock.
        Body: {"quantity": 5}
        """
        variant = self.get_object()
        quantity = request.data.get('quantity')
        
        if not quantity or quantity <= 0:
            return Response(
                {'error': 'Valid quantity required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        variant.release_stock(quantity)
        return Response({
            'message': f'Released {quantity} units',
            'new_stock': variant.stock
        })


class AdminProductImageViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for product images.
    Requires admin authentication.
    """
    permission_classes = [IsAdminUser]
    queryset = ProductImage.objects.all().select_related('product')
    serializer_class = ProductImageSerializer
    filterset_fields = ['product']
    ordering = ['product', 'order']
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        POST /api/admin/images/{id}/set_primary/
        Set this image as primary for its product.
        """
        image = self.get_object()
        image.is_primary = True
        image.save()
        return Response({
            'message': 'Image set as primary',
            'image_id': image.id
        })
