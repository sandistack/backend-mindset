"""
Celery tasks for background report generation.
"""

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone
import logging

from reports.services.excel_service import ExcelService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_export_task(self, job_id):
    """
    Generate export file in background.
    
    Args:
        job_id: ExportJob ID
    """
    from .models import ExportJob
    from .services.excel_service import ExcelService
    from apps.orders.models import Order
    from apps.products.models import Product
    
    try:
        job = ExportJob.objects.get(pk=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        logger.info(f"Starting export job {job_id}: {job.export_type}")
        
        # Generate based on export type
        if job.export_type == 'sales':
            buffer = generate_sales_export(job.filters)
            filename = f"sales_export_{job.id}.xlsx"
        
        elif job.export_type == 'products':
            buffer = generate_products_export(job.filters)
            filename = f"products_export_{job.id}.xlsx"
        
        elif job.export_type == 'orders':
            buffer = generate_orders_export(job.filters)
            filename = f"orders_export_{job.id}.xlsx"
        
        else:
            raise ValueError(f"Unknown export type: {job.export_type}")
        
        # Save file
        job.file.save(filename, ContentFile(buffer.getvalue()), save=False)
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Export job {job_id} completed successfully")
        
        # Optional: Send email notification
        # from apps.core.services.email_service import EmailService
        # EmailService.send_export_ready(job)
        
    except ExportJob.DoesNotExist:
        logger.error(f"Export job {job_id} not found")
    
    except Exception as exc:
        logger.error(f"Export job {job_id} failed: {str(exc)}")
        
        try:
            job = ExportJob.objects.get(pk=job_id)
            job.status = 'failed'
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save()
        except:
            pass
        
        # Retry on failure
        raise self.retry(exc=exc, countdown=60)


def generate_sales_export(filters):
    """Generate sales report Excel."""
    from apps.orders.models import Order
    
    orders = Order.objects.filter(
        status__in=['paid', 'processing', 'shipped', 'delivered', 'completed']
    ).select_related('user')
    
    # Apply filters
    if filters.get('date_from'):
        orders = orders.filter(created_at__gte=filters['date_from'])
    if filters.get('date_to'):
        orders = orders.filter(created_at__lte=filters['date_to'])
    if filters.get('status'):
        orders = orders.filter(status=filters['status'])
    
    orders = orders.order_by('-created_at')
    
    # Prepare data
    headers = [
        'Order Number', 'Date', 'Customer', 'Email', 'Status',
        'Items', 'Subtotal', 'Discount', 'Shipping', 'Total'
    ]
    data = []
    
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
    
    # Generate Excel
    excel = ExcelService()
    excel.set_title('Sales Report')
    excel.set_headers(headers)
    excel.add_rows(data)
    excel.auto_width()
    
    return excel.get_buffer()


def generate_products_export(filters):
    """Generate products report Excel."""
    from apps.products.models import Product
    
    products = Product.objects.filter(
        is_active=True
    ).prefetch_related('variants', 'category').order_by('name')
    
    # Prepare data
    headers = [
        'Product Name', 'SKU', 'Category', 'Variant',
        'Price', 'Stock', 'Status'
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
    
    return excel.get_buffer()


def generate_orders_export(filters):
    """Generate orders report Excel."""
    from apps.orders.models import Order
    
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    
    # Apply filters
    if filters.get('date_from'):
        orders = orders.filter(created_at__gte=filters['date_from'])
    if filters.get('date_to'):
        orders = orders.filter(created_at__lte=filters['date_to'])
    if filters.get('status'):
        orders = orders.filter(status=filters['status'])
    
    # Prepare data
    headers = [
        'Order Number', 'Date', 'Customer', 'Status',
        'Total', 'Payment Date', 'Shipping Date'
    ]
    data = []
    
    for order in orders:
        data.append([
            order.order_number,
            order.created_at,
            order.user.get_full_name() or order.user.email,
            order.get_status_display(),
            float(order.total),
            order.paid_at,
            order.shipped_at
        ])
    
    # Generate Excel
    excel = ExcelService()
    excel.set_title('Orders Report')
    excel.set_headers(headers)
    excel.add_rows(data)
    excel.auto_width()
    
    return excel.get_buffer()
