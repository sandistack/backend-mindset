"""
Order URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CheckoutView, OrderViewSet, AdminOrderViewSet


# Customer order endpoints
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

# Admin order endpoints
admin_router = DefaultRouter()
admin_router.register(r'orders', AdminOrderViewSet, basename='admin-order')

urlpatterns = [
    # Checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Customer orders
    path('', include(router.urls)),
    
    # Admin orders
    path('admin/', include(admin_router.urls)),
]
