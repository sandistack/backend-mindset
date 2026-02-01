# 📊 EXPORT - Django (Junior → Senior)

Dokumentasi lengkap tentang export data ke berbagai format: CSV, Excel, dan PDF.

---

## 🎯 Kapan Butuh Export?

```
Use Cases:
✅ Export laporan keuangan (PDF)
✅ Download data user (CSV/Excel)
✅ Generate invoice/receipt (PDF)
✅ Backup data (CSV)
✅ Analytics reports (Excel)
✅ Slip gaji (PDF)
✅ Certificate generation (PDF)
```

---

## 1️⃣ JUNIOR LEVEL - CSV Export

### Simple CSV Export

```python
# apps/tasks/views.py
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from .models import Task

class TaskCSVExportView(APIView):
    """
    Export tasks to CSV
    GET /api/tasks/export/csv/
    """
    
    def get(self, request):
        # Create response with CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tasks.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header
        writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Created At'])
        
        # Write data
        tasks = Task.objects.filter(user=request.user)
        for task in tasks:
            writer.writerow([
                task.id,
                task.title,
                task.status,
                task.priority,
                task.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
```

### CSV Export dengan Filtering

```python
# apps/tasks/views.py
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from .models import Task

class TaskCSVExportView(APIView):
    """
    Export tasks dengan filter
    GET /api/tasks/export/csv/?status=done&priority=high
    """
    
    def get(self, request):
        # Get filters from query params
        status = request.query_params.get('status')
        priority = request.query_params.get('priority')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Build queryset
        queryset = Task.objects.filter(user=request.user)
        
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Create response
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'
        
        # Write BOM for Excel compatibility
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Description', 'Status', 'Priority', 'Created At'])
        
        for task in queryset:
            writer.writerow([
                task.id,
                task.title,
                task.description or '',
                task.get_status_display(),
                task.get_priority_display(),
                task.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
```

---

## 2️⃣ MID LEVEL - Excel Export

### Install openpyxl

```bash
pip install openpyxl
```

### Excel Export dengan Styling

```python
# apps/core/services/excel_service.py
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from io import BytesIO


class ExcelService:
    """
    Service untuk generate Excel files
    """
    
    # Styles
    HEADER_FONT = Font(bold=True, color='FFFFFF')
    HEADER_FILL = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    HEADER_ALIGNMENT = Alignment(horizontal='center', vertical='center')
    
    BORDER = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    def __init__(self):
        self.workbook = Workbook()
        self.sheet = self.workbook.active
    
    def set_sheet_title(self, title: str):
        self.sheet.title = title
    
    def write_header(self, headers: list, row: int = 1):
        """
        Write styled header row
        """
        for col, header in enumerate(headers, 1):
            cell = self.sheet.cell(row=row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.HEADER_ALIGNMENT
            cell.border = self.BORDER
    
    def write_data(self, data: list, start_row: int = 2):
        """
        Write data rows
        """
        for row_idx, row_data in enumerate(data, start_row):
            for col_idx, value in enumerate(row_data, 1):
                cell = self.sheet.cell(row=row_idx, column=col_idx, value=value)
                cell.border = self.BORDER
    
    def auto_width(self):
        """
        Auto-adjust column widths
        """
        for column in self.sheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            self.sheet.column_dimensions[column_letter].width = adjusted_width
    
    def add_sheet(self, title: str):
        """
        Add new sheet
        """
        self.sheet = self.workbook.create_sheet(title=title)
    
    def get_response(self, filename: str) -> HttpResponse:
        """
        Return as HTTP response
        """
        self.auto_width()
        
        buffer = BytesIO()
        self.workbook.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        return response
    
    def save_to_file(self, filepath: str):
        """
        Save to file
        """
        self.auto_width()
        self.workbook.save(filepath)
```

### Excel Export View

```python
# apps/tasks/views.py
from rest_framework.views import APIView
from apps.core.services.excel_service import ExcelService
from .models import Task

class TaskExcelExportView(APIView):
    """
    Export tasks to Excel
    GET /api/tasks/export/excel/
    """
    
    def get(self, request):
        excel = ExcelService()
        excel.set_sheet_title('Tasks')
        
        # Headers
        headers = ['ID', 'Title', 'Description', 'Status', 'Priority', 'Created At', 'Due Date']
        excel.write_header(headers)
        
        # Data
        tasks = Task.objects.filter(user=request.user).select_related('user')
        data = []
        
        for task in tasks:
            data.append([
                task.id,
                task.title,
                task.description or '',
                task.get_status_display(),
                task.get_priority_display(),
                task.created_at.strftime('%Y-%m-%d %H:%M'),
                task.due_date.strftime('%Y-%m-%d') if task.due_date else ''
            ])
        
        excel.write_data(data)
        
        return excel.get_response('tasks_export')
```

### Multi-Sheet Excel Report

```python
# apps/reports/views.py
from rest_framework.views import APIView
from apps.core.services.excel_service import ExcelService
from apps.tasks.models import Task
from apps.users.models import User
from django.db.models import Count

class MonthlyReportExcelView(APIView):
    """
    Generate monthly report dengan multiple sheets
    """
    
    def get(self, request):
        excel = ExcelService()
        
        # Sheet 1: Summary
        excel.set_sheet_title('Summary')
        excel.write_header(['Metric', 'Value'])
        
        summary_data = [
            ['Total Users', User.objects.count()],
            ['Total Tasks', Task.objects.count()],
            ['Completed Tasks', Task.objects.filter(status='done').count()],
            ['Pending Tasks', Task.objects.filter(status='pending').count()],
        ]
        excel.write_data(summary_data)
        
        # Sheet 2: Tasks by User
        excel.add_sheet('Tasks by User')
        excel.write_header(['User', 'Total Tasks', 'Completed', 'Pending'])
        
        user_stats = User.objects.annotate(
            total=Count('tasks'),
            completed=Count('tasks', filter=models.Q(tasks__status='done')),
            pending=Count('tasks', filter=models.Q(tasks__status='pending'))
        )
        
        user_data = []
        for user in user_stats:
            user_data.append([
                user.username,
                user.total,
                user.completed,
                user.pending
            ])
        excel.write_data(user_data)
        
        # Sheet 3: All Tasks
        excel.add_sheet('All Tasks')
        excel.write_header(['ID', 'User', 'Title', 'Status', 'Created At'])
        
        tasks = Task.objects.select_related('user').all()
        task_data = [[t.id, t.user.username, t.title, t.status, t.created_at.strftime('%Y-%m-%d')] for t in tasks]
        excel.write_data(task_data)
        
        return excel.get_response('monthly_report')
```

---

## 3️⃣ MID-SENIOR LEVEL - PDF Export

### Install ReportLab & WeasyPrint

```bash
# Option 1: ReportLab (pure Python, simple PDFs)
pip install reportlab

# Option 2: WeasyPrint (HTML to PDF, complex layouts)
pip install weasyprint
```

### PDF Service dengan ReportLab

```python
# apps/core/services/pdf_service.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from django.http import HttpResponse
from io import BytesIO


class PDFService:
    """
    Service untuk generate PDF documents
    """
    
    def __init__(self, pagesize=A4):
        self.buffer = BytesIO()
        self.pagesize = pagesize
        self.styles = getSampleStyleSheet()
        self.elements = []
        
        # Custom styles
        self.styles.add(ParagraphStyle(
            name='Title',
            parent=self.styles['Heading1'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=20
        ))
    
    def add_title(self, text: str):
        self.elements.append(Paragraph(text, self.styles['Title']))
    
    def add_subtitle(self, text: str):
        self.elements.append(Paragraph(text, self.styles['Subtitle']))
    
    def add_paragraph(self, text: str, style: str = 'Normal'):
        self.elements.append(Paragraph(text, self.styles[style]))
        self.elements.append(Spacer(1, 12))
    
    def add_spacer(self, height: float = 0.5):
        self.elements.append(Spacer(1, height * inch))
    
    def add_table(self, data: list, col_widths: list = None, header: bool = True):
        """
        Add styled table
        """
        table = Table(data, colWidths=col_widths)
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ])
        
        # Alternate row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F2F2F2'))
        
        table.setStyle(style)
        self.elements.append(table)
        self.elements.append(Spacer(1, 20))
    
    def add_image(self, image_path: str, width: float = 2, height: float = 2):
        img = Image(image_path, width=width*inch, height=height*inch)
        self.elements.append(img)
    
    def build(self) -> BytesIO:
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        doc.build(self.elements)
        self.buffer.seek(0)
        return self.buffer
    
    def get_response(self, filename: str) -> HttpResponse:
        self.build()
        
        response = HttpResponse(
            self.buffer.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        
        return response
```

### Invoice PDF Example

```python
# apps/billing/services/invoice_service.py
from apps.core.services.pdf_service import PDFService
from reportlab.lib.units import inch
from datetime import datetime


class InvoiceService:
    """
    Generate invoice PDFs
    """
    
    def generate_invoice(self, invoice) -> PDFService:
        pdf = PDFService()
        
        # Header
        pdf.add_title('INVOICE')
        pdf.add_subtitle(f'Invoice #{invoice.number}')
        
        # Company Info
        pdf.add_paragraph(f'''
            <b>From:</b><br/>
            Your Company Name<br/>
            123 Business Street<br/>
            City, Country 12345<br/>
            Email: billing@company.com
        ''')
        
        pdf.add_spacer(0.3)
        
        # Customer Info
        pdf.add_paragraph(f'''
            <b>Bill To:</b><br/>
            {invoice.customer.name}<br/>
            {invoice.customer.address}<br/>
            {invoice.customer.email}
        ''')
        
        pdf.add_spacer(0.3)
        
        # Invoice Details
        pdf.add_paragraph(f'''
            <b>Invoice Date:</b> {invoice.created_at.strftime('%B %d, %Y')}<br/>
            <b>Due Date:</b> {invoice.due_date.strftime('%B %d, %Y')}<br/>
            <b>Status:</b> {invoice.get_status_display()}
        ''')
        
        pdf.add_spacer(0.5)
        
        # Items Table
        table_data = [['Description', 'Qty', 'Unit Price', 'Total']]
        
        for item in invoice.items.all():
            table_data.append([
                item.description,
                str(item.quantity),
                f'${item.unit_price:,.2f}',
                f'${item.total:,.2f}'
            ])
        
        # Subtotal, Tax, Total
        table_data.append(['', '', 'Subtotal:', f'${invoice.subtotal:,.2f}'])
        table_data.append(['', '', f'Tax ({invoice.tax_rate}%):', f'${invoice.tax_amount:,.2f}'])
        table_data.append(['', '', 'Total:', f'${invoice.total:,.2f}'])
        
        pdf.add_table(table_data, col_widths=[3*inch, 0.7*inch, 1.2*inch, 1.2*inch])
        
        # Footer
        pdf.add_spacer(0.5)
        pdf.add_paragraph('''
            <b>Payment Terms:</b> Net 30 days<br/>
            <b>Bank:</b> Bank Name - Account: 1234567890<br/>
            <br/>
            Thank you for your business!
        ''')
        
        return pdf
```

### Invoice View

```python
# apps/billing/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Invoice
from .services.invoice_service import InvoiceService

class InvoicePDFView(APIView):
    """
    Generate invoice PDF
    GET /api/invoices/{id}/pdf/
    """
    
    def get(self, request, pk):
        try:
            invoice = Invoice.objects.get(pk=pk, user=request.user)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=404)
        
        invoice_service = InvoiceService()
        pdf = invoice_service.generate_invoice(invoice)
        
        return pdf.get_response(f'invoice_{invoice.number}')
```

---

## 4️⃣ SENIOR LEVEL - WeasyPrint (HTML to PDF)

### HTML Template untuk PDF

```html
<!-- templates/pdf/invoice.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #4472C4;
        }
        
        .invoice-info {
            text-align: right;
        }
        
        .invoice-number {
            font-size: 18px;
            font-weight: bold;
        }
        
        .addresses {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        
        .address-block {
            width: 45%;
        }
        
        .address-block h3 {
            margin-bottom: 10px;
            color: #4472C4;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        
        th {
            background-color: #4472C4;
            color: white;
            padding: 12px;
            text-align: left;
        }
        
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .totals {
            float: right;
            width: 300px;
        }
        
        .totals table {
            margin-bottom: 0;
        }
        
        .totals td {
            border: none;
        }
        
        .grand-total {
            font-size: 16px;
            font-weight: bold;
            background-color: #4472C4 !important;
            color: white;
        }
        
        .footer {
            clear: both;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            Your Company
        </div>
        <div class="invoice-info">
            <div class="invoice-number">Invoice #{{ invoice.number }}</div>
            <div>Date: {{ invoice.created_at|date:"F d, Y" }}</div>
            <div>Due: {{ invoice.due_date|date:"F d, Y" }}</div>
        </div>
    </div>
    
    <div class="addresses">
        <div class="address-block">
            <h3>From</h3>
            <p>
                Your Company Name<br>
                123 Business Street<br>
                City, Country 12345<br>
                billing@company.com
            </p>
        </div>
        <div class="address-block">
            <h3>Bill To</h3>
            <p>
                {{ invoice.customer.name }}<br>
                {{ invoice.customer.address }}<br>
                {{ invoice.customer.email }}
            </p>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in invoice.items.all %}
            <tr>
                <td>{{ item.description }}</td>
                <td>{{ item.quantity }}</td>
                <td>${{ item.unit_price|floatformat:2 }}</td>
                <td>${{ item.total|floatformat:2 }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="totals">
        <table>
            <tr>
                <td>Subtotal:</td>
                <td>${{ invoice.subtotal|floatformat:2 }}</td>
            </tr>
            <tr>
                <td>Tax ({{ invoice.tax_rate }}%):</td>
                <td>${{ invoice.tax_amount|floatformat:2 }}</td>
            </tr>
            <tr class="grand-total">
                <td>Total:</td>
                <td>${{ invoice.total|floatformat:2 }}</td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Thank you for your business!</p>
        <p>Payment Terms: Net 30 days | Bank: Bank Name - Account: 1234567890</p>
    </div>
</body>
</html>
```

### WeasyPrint Service

```python
# apps/core/services/weasyprint_service.py
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.http import HttpResponse
from io import BytesIO


class WeasyPrintService:
    """
    Generate PDF from HTML templates using WeasyPrint
    """
    
    def generate_pdf(
        self,
        template_name: str,
        context: dict,
        css_files: list = None
    ) -> BytesIO:
        """
        Generate PDF from Django template
        """
        # Render HTML
        html_string = render_to_string(template_name, context)
        
        # Create HTML object
        html = HTML(string=html_string)
        
        # Add CSS if provided
        stylesheets = []
        if css_files:
            for css_file in css_files:
                stylesheets.append(CSS(filename=css_file))
        
        # Generate PDF
        buffer = BytesIO()
        html.write_pdf(buffer, stylesheets=stylesheets)
        buffer.seek(0)
        
        return buffer
    
    def get_response(
        self,
        template_name: str,
        context: dict,
        filename: str,
        css_files: list = None
    ) -> HttpResponse:
        """
        Return PDF as HTTP response
        """
        buffer = self.generate_pdf(template_name, context, css_files)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        
        return response
```

### WeasyPrint View

```python
# apps/billing/views.py
from rest_framework.views import APIView
from apps.core.services.weasyprint_service import WeasyPrintService
from .models import Invoice

class InvoicePDFView(APIView):
    """
    Generate invoice PDF using WeasyPrint
    """
    
    def get(self, request, pk):
        invoice = Invoice.objects.get(pk=pk, user=request.user)
        
        pdf_service = WeasyPrintService()
        
        return pdf_service.get_response(
            template_name='pdf/invoice.html',
            context={'invoice': invoice},
            filename=f'invoice_{invoice.number}'
        )
```

---

## 5️⃣ EXPERT LEVEL - Background Export untuk Large Data

### Celery Task untuk Export

```python
# apps/exports/tasks.py
from celery import shared_task
from django.core.files.base import ContentFile
from apps.core.services.excel_service import ExcelService
from apps.exports.models import ExportJob
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_export_task(self, export_job_id: int):
    """
    Background task untuk generate export file
    """
    from apps.tasks.models import Task
    
    try:
        job = ExportJob.objects.get(id=export_job_id)
        job.status = 'processing'
        job.save()
        
        # Get data berdasarkan filters
        queryset = Task.objects.filter(**job.filters)
        total = queryset.count()
        
        # Generate Excel
        excel = ExcelService()
        excel.set_sheet_title('Export')
        excel.write_header(['ID', 'Title', 'Status', 'Created At'])
        
        data = []
        for idx, task in enumerate(queryset.iterator(chunk_size=1000)):
            data.append([task.id, task.title, task.status, str(task.created_at)])
            
            # Update progress setiap 1000 records
            if idx % 1000 == 0:
                job.progress = int((idx / total) * 100)
                job.save()
        
        excel.write_data(data)
        
        # Save file
        buffer = excel.build()
        job.file.save(
            f'export_{job.id}.xlsx',
            ContentFile(buffer.getvalue())
        )
        
        job.status = 'completed'
        job.progress = 100
        job.save()
        
        # Send notification email
        from apps.core.services.email_service import EmailService
        EmailService().send_email(
            to_email=job.user.email,
            subject='Your export is ready',
            template_name='export_ready',
            context={'job': job}
        )
        
        return {'status': 'success', 'job_id': job.id}
        
    except Exception as e:
        logger.error(f'Export failed: {e}')
        job.status = 'failed'
        job.error_message = str(e)
        job.save()
        raise
```

### Export Job Model

```python
# apps/exports/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ExportJob(models.Model):
    """
    Track export jobs
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    export_type = models.CharField(max_length=50)  # 'tasks', 'users', etc.
    format = models.CharField(max_length=10)  # 'csv', 'excel', 'pdf'
    filters = models.JSONField(default=dict)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    progress = models.PositiveSmallIntegerField(default=0)
    
    file = models.FileField(upload_to='exports/', null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['-created_at']
```

### Export API

```python
# apps/exports/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ExportJob
from .serializers import ExportJobSerializer
from .tasks import generate_export_task


class ExportJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExportJobSerializer
    
    def get_queryset(self):
        return ExportJob.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_export(self, request):
        """
        Create new export job
        POST /api/exports/create_export/
        Body: { "export_type": "tasks", "format": "excel", "filters": {"status": "done"} }
        """
        export_type = request.data.get('export_type')
        export_format = request.data.get('format', 'excel')
        filters = request.data.get('filters', {})
        
        # Create job
        job = ExportJob.objects.create(
            user=request.user,
            export_type=export_type,
            format=export_format,
            filters=filters
        )
        
        # Start background task
        generate_export_task.delay(job.id)
        
        return Response({
            'job_id': job.id,
            'status': 'pending',
            'message': 'Export job created. You will be notified when ready.'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download export file
        GET /api/exports/{id}/download/
        """
        job = self.get_object()
        
        if job.status != 'completed':
            return Response(
                {'error': f'Export is {job.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate presigned URL or redirect to file
        return Response({
            'download_url': request.build_absolute_uri(job.file.url)
        })
```

---

## 📋 Quick Reference

### Export Format Comparison

| Format | Best For | Library |
|--------|----------|---------|
| **CSV** | Simple data, large files | Built-in `csv` |
| **Excel** | Formatted reports, multiple sheets | `openpyxl` |
| **PDF** | Invoices, certificates, formal docs | `reportlab`, `weasyprint` |

### Export Checklist

```
□ Add proper headers and metadata
□ Handle large datasets with streaming/chunking
□ Use background tasks for big exports
□ Set proper Content-Type and filename
□ Add progress tracking for long exports
□ Cleanup old export files periodically
□ Log all export activities
□ Consider file size limits
□ Add export to audit log
□ Send notification when complete
```

---

## 🔗 Related Docs

- [BACKGROUND_JOBS.md](BACKGROUND_JOBS.md) - Async exports
- [FILE_UPLOAD.md](FILE_UPLOAD.md) - Store export files
- [EMAIL.md](EMAIL.md) - Send export notifications
