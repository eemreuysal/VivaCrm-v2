"""
PDF generation functionality for invoices.
"""
import io
import os
import uuid
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils import timezone
import logging
import tempfile
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if weasyprint is available, otherwise use a fallback
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint is not installed. PDF generation will be limited to HTML.")


class PDFGenerator:
    """
    Class for generating PDF files from HTML.
    """
    
    @staticmethod
    def generate_pdf_from_html(html_content, filename=None):
        """
        Generate a PDF file from HTML content.
        
        Args:
            html_content: HTML string content
            filename: Optional filename for the PDF (without extension)
            
        Returns:
            Tuple of (file_content, filename) or None if generation fails
        """
        if not WEASYPRINT_AVAILABLE:
            logger.warning("PDF generation failed: WeasyPrint not installed.")
            return None, None

        try:
            # Generate PDF using WeasyPrint
            pdf_file = io.BytesIO()
            HTML(string=html_content).write_pdf(pdf_file)
            pdf_file.seek(0)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"document_{timestamp}"
                
            return pdf_file.getvalue(), f"{filename}.pdf"
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return None, None
    
    @staticmethod
    def save_pdf_to_file(pdf_content, filename, directory=None):
        """
        Save PDF content to a file.
        
        Args:
            pdf_content: Binary PDF content
            filename: Filename for the PDF (with or without extension)
            directory: Directory to save the file (default: MEDIA_ROOT/pdfs)
            
        Returns:
            Path to the saved file or None if saving fails
        """
        if not pdf_content:
            return None
            
        try:
            # Ensure filename has .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename = f"{filename}.pdf"
                
            # Determine directory
            if not directory:
                directory = os.path.join(settings.MEDIA_ROOT, 'pdfs')
                
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Create full path
            file_path = os.path.join(directory, filename)
            
            # Write PDF to file
            with open(file_path, 'wb') as f:
                f.write(pdf_content)
                
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save PDF to file: {str(e)}")
            return None


class InvoicePDFGenerator:
    """
    Class for generating PDF invoices.
    """
    
    @staticmethod
    def generate_invoice_html(invoice, context=None):
        """
        Generate HTML content for an invoice.
        
        Args:
            invoice: The Invoice object
            context: Additional context data for the template
            
        Returns:
            HTML content string
        """
        # Prepare context for template
        ctx = {
            'invoice': invoice,
            'order': invoice.order,
            'customer': invoice.order.customer,
            'items': invoice.items.all(),
            'company': {
                'name': 'VivaCRM Ltd.',
                'address': 'İstanbul, Türkiye',
                'phone': '+90 212 123 4567',
                'email': 'info@vivacrm.com',
                'website': 'www.vivacrm.com',
                'tax_id': '1234567890',
            }
        }
        
        # Add any additional context
        if context:
            ctx.update(context)
        
        # Render HTML
        html_string = render_to_string('invoices/pdf/invoice_template.html', ctx)
        return html_string
    
    @staticmethod
    def generate_invoice_pdf(invoice, context=None, save_to_model=True):
        """
        Generate a PDF for an invoice.
        
        Args:
            invoice: The Invoice object
            context: Additional context data for the template
            save_to_model: Whether to save the PDF file to the invoice model
            
        Returns:
            Tuple of (pdf_content, filename) or (None, None) if generation fails
        """
        # Generate HTML content
        html_content = InvoicePDFGenerator.generate_invoice_html(invoice, context)
        
        # Save HTML content to invoice
        invoice.html_content = html_content
        invoice.save(update_fields=['html_content'])
        
        # If WeasyPrint is not available, return only HTML
        if not WEASYPRINT_AVAILABLE:
            return None, None
            
        # Generate filename
        filename = f"invoice_{invoice.invoice_number}_{timezone.now().strftime('%Y%m%d')}"
        
        # Generate PDF
        pdf_content, full_filename = PDFGenerator.generate_pdf_from_html(html_content, filename)
        
        # If requested and successful, save to invoice model
        if save_to_model and pdf_content:
            # Create directory
            pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices', str(invoice.id))
            os.makedirs(pdf_dir, exist_ok=True)
            
            # Save file
            file_path = PDFGenerator.save_pdf_to_file(pdf_content, full_filename, pdf_dir)
            
            # Update invoice model with file path (relative to MEDIA_ROOT)
            if file_path:
                rel_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                invoice.pdf_file = rel_path
                invoice.save(update_fields=['pdf_file'])
        
        return pdf_content, full_filename