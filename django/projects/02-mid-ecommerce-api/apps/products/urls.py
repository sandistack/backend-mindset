"""
URL routing for Products app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router for admin viewsets
admin_router = DefaultRouter()
admin_router.register(r'products', views.AdminProductViewSet, basename='admin-product')
admin_router.register(r'categories', views.AdminCategoryViewSet, basename='admin-category')
admin_router.register(r'variants', views.AdminProductVariantViewSet, basename='admin-variant')
admin_router.register(r'images', views.AdminProductImageViewSet, basename='admin-image')

# Public URLs
urlpatterns = [
    # Public endpoints (no auth required)
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Admin endpoints (IsAdminUser required)
    path('admin/', include(admin_router.urls)),
    
    # Image upload endpoints
    path('admin/products/<int:product_id>/upload-image/', 
         views.ProductImageUploadView.as_view(), 
         name='product-image-upload'),
    path('admin/products/<int:product_id>/images/<int:image_id>/', 
         views.ProductImageUploadView.as_view(), 
         name='product-image-delete'),
    path('admin/products/<int:product_id>/images/reorder/', 
         views.ProductImageReorderView.as_view(), 
         name='product-image-reorder'),
]
