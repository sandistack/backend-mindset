"""
Reports URLs.
"""

from django.urls import path
from .views import (
    SalesReportExcelView,
    ProductsReportExcelView,
    InvoicePDFView,
)

urlpatterns = [
    # Admin reports
    path('admin/reports/sales/export/', SalesReportExcelView.as_view(), name='sales-export'),
    path('admin/reports/products/export/', ProductsReportExcelView.as_view(), name='products-export'),
    
    # Invoice (customer can access their own)
    path('orders/<int:order_id>/invoice/', InvoicePDFView.as_view(), name='order-invoice'),
]
