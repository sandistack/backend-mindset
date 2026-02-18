"""
PDF invoice generation service using ReportLab.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from django.conf import settings


class InvoicePDFService:
    """Service for generating PDF invoices."""
    
    def __init__(self, order):
        self.order = order
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#4472C4'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4472C4'),
            spaceAfter=10
        )
        
        self.footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
    
    def generate(self):
        """
        Generate invoice PDF.
        
        Returns:
            BytesIO: PDF buffer
        """
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
        elements.append(Paragraph("INVOICE", self.title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Invoice info table
        info_data = [
            ['Invoice Number:', self.order.order_number],
            ['Date:', self.order.created_at.strftime('%d %B %Y')],
            ['Status:', self.order.get_status_display().upper()],
        ]
        
        if self.order.paid_at:
            info_data.append(['Payment Date:', self.order.paid_at.strftime('%d %B %Y')])
        
        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4472C4')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))
        
        # Customer info section
        elements.append(Paragraph("Bill To:", self.heading_style))
        bill_to = [
            f"<b>{self.order.shipping_name}</b>",
            self.order.shipping_address,
            f"{self.order.shipping_city} {self.order.shipping_postal_code}",
            f"Phone: {self.order.shipping_phone}",
            f"Email: {self.order.user.email}"
        ]
        for line in bill_to:
            elements.append(Paragraph(line, self.styles['Normal']))
        elements.append(Spacer(1, 1*cm))
        
        # Items table
        elements.append(Paragraph("Order Items:", self.heading_style))
        
        table_data = [['Product', 'Qty', 'Price', 'Subtotal']]
        
        for item in self.order.items.select_related('variant__product').all():
            table_data.append([
                f"{item.product_name}\n{item.variant_name}",
                str(item.quantity),
                f"Rp {item.price:,.0f}",
                f"Rp {item.subtotal:,.0f}"
            ])
        
        # Add spacing row
        table_data.append(['', '', '', ''])
        
        # Totals
        table_data.append(['', '', 'Subtotal:', f"Rp {self.order.subtotal:,.0f}"])
        
        if self.order.discount_amount > 0:
            table_data.append(['', '', 'Discount:', f"-Rp {self.order.discount_amount:,.0f}"])
        
        table_data.append(['', '', 'Shipping:', f"Rp {self.order.shipping_cost:,.0f}"])
        table_data.append(['', '', 'TOTAL:', f"Rp {self.order.total:,.0f}"])
        
        items_table = Table(table_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Body rows
            ('FONTNAME', (0, 1), (-1, -5), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -5), 'LEFT'),
            
            # Grid for items
            ('GRID', (0, 0), (-1, -5), 0.5, colors.grey),
            
            # Totals section
            ('FONTNAME', (2, -4), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (2, -1), (-1, -1), 2, colors.black),
            ('FONTSIZE', (2, -1), (-1, -1), 12),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 2*cm))
        
        # Footer
        elements.append(Paragraph(
            f"Thank you for your purchase!<br/>", 
            self.footer_style
        ))
        elements.append(Paragraph(
            f"© {self.order.created_at.year} {settings.SITE_NAME}. All rights reserved.", 
            self.footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer
