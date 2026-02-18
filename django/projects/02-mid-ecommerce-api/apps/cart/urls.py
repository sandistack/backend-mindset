"""
URL routing for Cart app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Cart endpoints
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/items/', views.CartItemView.as_view(), name='cart-items'),
    path('cart/items/<int:item_id>/', views.CartItemView.as_view(), name='cart-item-detail'),
    path('cart/discount/', views.ApplyDiscountView.as_view(), name='cart-discount'),
]
