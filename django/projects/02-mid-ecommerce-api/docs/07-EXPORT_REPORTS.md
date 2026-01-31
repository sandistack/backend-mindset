# 📊 Step 7: Export Reports

**Waktu:** 4-6 jam  
**Prerequisite:** Step 6 selesai

---

## 🎯 Tujuan

- Export sales report ke Excel
- Export invoice ke PDF
- Background export untuk data besar
- Download management

---

## 📋 Tasks

### 7.1 Install Dependencies

```bash
pip install openpyxl reportlab weasyprint
```

### 7.2 Excel Export Service

**Buat `apps/reports/services/excel_service.py`:**

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from io import BytesIO
from datetime import datetime

class ExcelService:
    
    def __init__(self):
        self.wb = Workbook()
        self.ws = self.wb.active
        
        # Styles
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    def set_title(self, title):
        """Set worksheet title"""
        self.ws.title = title
        return self
    
    def set_headers(self, headers):
        """Set header row with styling"""
        for col, header in enumerate(headers, 1):
            cell = self.ws.cell(row=1, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border
        return self
    
    def add_rows(self, data):
        """Add data rows"""
        for row_num, row_data in enumerate(data, 2):
            for col_num, value in enumerate(row_data, 1):
                cell = self.ws.cell(row=row_num, column=col_num, value=value)
                cell.border = self.border
                
                # Format dates
                if isinstance(value, datetime):
                    cell.number_format = 'YYYY-MM-DD HH:MM'
                # Format currency
                elif isinstance(value, (int, float)) and col_num > 2:
                    cell.number_format = '#,##0'
        return self
    
    def auto_width(self):
        """Auto-adjust column widths"""
        for col in range(1, self.ws.max_column + 1):
            max_length = 0
            column = get_column_letter(col)
            
            for cell in self.ws[column]:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            self.ws.column_dimensions[column].width = adjusted_width
        return self
    
    def get_buffer(self):
        """Return BytesIO buffer"""
        buffer = BytesIO()
        self.wb.save(buffer)
        buffer.seek(0)
        return buffer
    
    def save(self, filepath):
        """Save to file"""
        self.wb.save(filepath)
```

### 7.3 PDF Invoice Service

**Buat `apps/reports/services/pdf_service.py`:**

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

class InvoicePDFService:
    
    def __init__(self, order):
        self.order = order
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
    
    def generate(self):
        """Generate invoice PDF"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=24,
            alignment=1  # Center
        )
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Invoice info
        info_data = [
            ['Invoice Number:', self.order.order_number],
            ['Date:', self.order.created_at.strftime('%d %B %Y')],
            ['Status:', self.order.status.upper()],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))
        
        # Customer info
        elements.append(Paragraph("Bill To:", self.styles['Heading3']))
        elements.append(Paragraph(f"{self.order.shipping_name}", self.styles['Normal']))
        elements.append(Paragraph(f"{self.order.shipping_address}", self.styles['Normal']))
        elements.append(Paragraph(f"{self.order.shipping_city} {self.order.shipping_postal_code}", self.styles['Normal']))
        elements.append(Paragraph(f"Phone: {self.order.shipping_phone}", self.styles['Normal']))
        elements.append(Spacer(1, 1*cm))
        
        # Items table
        table_data = [['Product', 'Qty', 'Price', 'Subtotal']]
        
        for item in self.order.items.all():
            table_data.append([
                f"{item.product_name}\n{item.variant_name}",
                str(item.quantity),
                f"Rp {item.price:,.0f}",
                f"Rp {item.subtotal:,.0f}"
            ])
        
        # Totals
        table_data.append(['', '', 'Subtotal:', f"Rp {self.order.subtotal:,.0f}"])
        if self.order.discount_amount:
            table_data.append(['', '', 'Discount:', f"-Rp {self.order.discount_amount:,.0f}"])
        table_data.append(['', '', 'Shipping:', f"Rp {self.order.shipping_cost:,.0f}"])
        table_data.append(['', '', 'TOTAL:', f"Rp {self.order.total:,.0f}"])
        
        items_table = Table(table_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Borders
            ('GRID', (0, 0), (-1, -5), 0.5, colors.grey),
            
            # Total row
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 2*cm))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph("Thank you for your purchase!", footer_style))
        
        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer
```

**Referensi:** [EXPORT.md](../../../docs/04-advanced/EXPORT.md)

### 7.4 Report Views

```python
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

class SalesReportExcelView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Export sales report to Excel"""
        # Get date range from query params
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        
        # Query orders
        orders = Order.objects.filter(
            status__in=['paid', 'shipped', 'completed']
        )
        
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
        
        orders = orders.order_by('-created_at')
        
        # Prepare data
        headers = ['Order Number', 'Date', 'Customer', 'Status', 'Subtotal', 'Discount', 'Total']
        data = []
        
        for order in orders:
            data.append([
                order.order_number,
                order.created_at,
                order.user.name,
                order.status,
                float(order.subtotal),
                float(order.discount_amount),
                float(order.total)
            ])
        
        # Generate Excel
        excel = ExcelService()
        excel.set_title('Sales Report')
        excel.set_headers(headers)
        excel.add_rows(data)
        excel.auto_width()
        
        buffer = excel.get_buffer()
        
        # Response
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=sales_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        
        return response


class InvoicePDFView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        """Generate invoice PDF"""
        order = get_object_or_404(Order, pk=order_id)
        
        # Check ownership
        if order.user != request.user and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=403)
        
        # Generate PDF
        pdf_service = InvoicePDFService(order)
        buffer = pdf_service.generate()
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=invoice_{order.order_number}.pdf'
        
        return response
```

### 7.5 Background Export (Large Data)

**Di `apps/reports/models.py`:**

```python
class ExportJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    export_type = models.CharField(max_length=50)  # sales, products, orders
    format = models.CharField(max_length=10)  # excel, csv
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file = models.FileField(upload_to='exports/', null=True, blank=True)
    error_message = models.TextField(blank=True)
    filters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

**Di `apps/reports/tasks.py`:**

```python
from celery import shared_task
from django.core.files.base import ContentFile

@shared_task(bind=True)
def generate_export(self, job_id):
    """Generate export in background"""
    from .models import ExportJob
    from .services.excel_service import ExcelService
    
    job = ExportJob.objects.get(pk=job_id)
    job.status = 'processing'
    job.save()
    
    try:
        if job.export_type == 'sales':
            buffer = generate_sales_report(job.filters)
        elif job.export_type == 'products':
            buffer = generate_products_report(job.filters)
        
        # Save file
        filename = f"{job.export_type}_{job.id}.xlsx"
        job.file.save(filename, ContentFile(buffer.getvalue()))
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
        # Optional: Send email notification
        # send_export_ready_email.delay(job.id)
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.save()
        raise
```

---

## 🗂️ API Endpoints

```
# Instant exports (small data)
GET    /api/admin/reports/sales/export/       # Sales Excel
GET    /api/orders/{id}/invoice/              # Invoice PDF

# Background exports (large data)
POST   /api/admin/reports/export/             # Create export job
GET    /api/admin/reports/export/{id}/        # Check status
GET    /api/admin/reports/export/{id}/download/  # Download file
```

---

## ✅ Checklist

- [ ] ExcelService with styling
- [ ] PDF Invoice service
- [ ] Sales report export
- [ ] Invoice PDF generation
- [ ] ExportJob model
- [ ] Background export task
- [ ] Download endpoint
- [ ] Date range filtering
- [ ] Admin-only access

---

## 🔗 Referensi

- [EXPORT.md](../../../docs/04-advanced/EXPORT.md) - Complete export guide
- [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md) - Celery

---

## ➡️ Next Step

Lanjut ke [08-PAYMENT_INTEGRATION.md](08-PAYMENT_INTEGRATION.md) - Payment Gateway
