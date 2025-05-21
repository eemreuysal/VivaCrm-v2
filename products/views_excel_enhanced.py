"""
Enhanced Product Excel Import View - Production-ready solution.
"""
import os
import json
import logging
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from products.excel_smart_import import import_products_smart
from products.forms import ProductImportForm
from accounts.decorators import permission_required
from products.tasks import import_products_task

logger = logging.getLogger(__name__)


@login_required
@permission_required(['products.add_product', 'products.change_product'])
def import_products_excel_enhanced(request):
    """
    Enhanced Excel import view with smart features:
    - Automatic category creation
    - Field validation and correction
    - Memory efficient processing
    - Comprehensive error handling
    """
    
    if request.method == 'POST':
        form = ProductImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                uploaded_file = request.FILES['file']
                
                # Log import start
                logger.info(f"Starting product import by user {request.user}")
                
                # Process file immediately for small files
                if uploaded_file.size < 1024 * 1024:  # 1MB
                    result = import_products_smart(
                        file_buffer=uploaded_file,
                        user=request.user
                    )
                    
                    # Show results
                    return render(request, 'products/import_results_enhanced.html', {
                        'result': result,
                        'title': _('İçe Aktarma Sonuçları')
                    })
                    
                else:
                    # Use async task for large files
                    # Save file temporarily
                    temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', f'import_{datetime.now().timestamp()}.xlsx')
                    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                    
                    with open(temp_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)
                            
                    # Start async task
                    task = import_products_task.delay(
                        file_path=temp_path,
                        user_id=request.user.id
                    )
                    
                    messages.info(request, _('Büyük dosya arka planda işleniyor. Sonuçlar e-posta ile gönderilecek.'))
                    
                    # Return task status page
                    return render(request, 'products/import_task_status.html', {
                        'task_id': task.id,
                        'title': _('İçe Aktarma Durumu')
                    })
                    
            except Exception as e:
                logger.error(f"Import error: {str(e)}")
                messages.error(request, f"İçe aktarma hatası: {str(e)}")
                
        else:
            messages.error(request, _('Lütfen geçerli bir Excel dosyası seçin.'))
            
    else:
        form = ProductImportForm()
        
    return render(request, 'products/product_import_enhanced.html', {
        'form': form,
        'title': _('Ürün İçe Aktarma')
    })


@login_required
@require_http_methods(['GET'])
def get_import_template(request):
    """Download Excel import template."""
    
    # Create sample template with headers
    import pandas as pd
    
    template_data = {
        'Ürün Adı': ['Örnek Ürün 1', 'Örnek Ürün 2'],
        'Ürün Kodu': ['URUN001', 'URUN002'],
        'Kategori': ['Elektronik', 'Giyim'],
        'Fiyat': [99.90, 149.50],
        'Stok': [100, 50],
        'SKU': ['SKU001', 'SKU002'],
        'Barkod': ['8690123456789', '8690987654321'],
        'Açıklama': ['Ürün açıklaması', 'Detaylı ürün bilgisi'],
        'Maliyet': [50.00, 75.00],
        'İndirimli Fiyat': ['', 129.90]
    }
    
    df = pd.DataFrame(template_data)
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=urun_import_sablonu.xlsx'
    
    # Write to Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Ürünler', index=False)
        
        # Add column descriptions
        worksheet = writer.sheets['Ürünler']
        
        # Add header styling
        from openpyxl.styles import Font, PatternFill
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="336699", end_color="336699", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            
        # Adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
    return response


@login_required
@require_http_methods(['GET'])
def check_import_status(request, task_id):
    """Check async import task status."""
    
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    response = {
        'task_id': task_id,
        'status': task.status,
        'current': 0,
        'total': 100,
        'result': None
    }
    
    if task.info:
        response.update(task.info)
        
    return JsonResponse(response)