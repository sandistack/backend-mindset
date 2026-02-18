"""
Report export views.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from datetime import datetime

from apps.orders.models import Order
from .services.excel_service import ExcelService
from .services.pdf_service import InvoicePDFService


class SalesReportExcelView(APIView):
    """Export sales report to Excel."""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """
        GET /api/admin/reports/sales/export/
        
        Query params:
        - from: Start date (YYYY-MM-DD)
        - to: End date (YYYY-MM-DD)
        - status: Filter by status
        """
        # Get filters from query params
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        status_filter = request.query_params.get('status')
        
        # Query orders
        orders = Order.objects.filter(
            status__in=['paid', 'processing', 'shipped', 'delivered', 'completed']
        ).select_related('user')
        
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        orders = orders.order_by('-created_at')
        
        # Prepare data
        headers = [
            'Order Number', 
            'Date', 
            'Customer', 
            'Email',
            'Status', 
            'Items',
            'Subtotal', 
            'Discount', 
            'Shipping',
            'Total'
        ]
        data = []
        total_revenue = 0
        
        for order in orders:
            data.append([
                order.order_number,
                order.created_at,
                order.user.get_full_name() or order.user.email,
                order.user.email,
                order.get_status_display(),
                order.items.count(),
                float(order.subtotal),
                float(order.discount_amount),
                float(order.shipping_cost),
                float(order.total)
            ])
            total_revenue += float(order.total)
        
        # Generate Excel
        excel = ExcelService()
        excel.set_title('Sales Report')
        excel.set_headers(headers)
        excel.add_rows(data)
        excel.auto_width()
        
        # Add summary
        if data:
            excel.add_summary_row(f'Total Orders: {len(data)}', total_revenue)
        
        buffer = excel.get_buffer()
        
        # Prepare response
        filename = f'sales_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response


class InvoicePDFView(APIView):
    """Generate invoice PDF for order."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        """
        GET /api/orders/{id}/invoice/
        
        Generate and download invoice PDF.
        """
        order = get_object_or_404(
            Order.objects.select_related('user').prefetch_related('items__variant__product'),
            pk=order_id
        )
        
        # Check ownership or admin
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=403
            )
        
        # Generate PDF
        pdf_service = InvoicePDFService(order)
        buffer = pdf_service.generate()
        
        # Prepare response
        filename = f'invoice_{order.order_number}.pdf'
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response


class ProductsReportExcelView(APIView):
    """Export products report to Excel."""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """
        GET /api/admin/reports/products/export/
        
        Export all products with stock and pricing info.
        """
        from apps.products.models import Product, ProductVariant
        
        # Query products
        products = Product.objects.filter(
            is_active=True
        ).prefetch_related('variants').order_by('name')
        
        # Prepare data
        headers = [
            'Product Name',
            'SKU',
            'Category',
            'Variant',
            'Price',
            'Stock',
            'Status'
        ]
        data = []
        
        for product in products:
            for variant in product.variants.all():
                data.append([
                    product.name,
                    variant.sku,
                    product.category.name if product.category else '-',
                    variant.name,
                    float(variant.price),
                    variant.stock,
                    'In Stock' if variant.stock > 0 else 'Out of Stock'
                ])
        
        # Generate Excel
        excel = ExcelService()
        excel.set_title('Products Report')
        excel.set_headers(headers)
        excel.add_rows(data)
        excel.auto_width()
        
        buffer = excel.get_buffer()
        
        # Prepare response
        filename = f'products_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
