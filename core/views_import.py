"""
Import geçmişi ve yeniden yükleme görüntüleme katmanı
"""
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import default_storage
from django.utils import timezone
from django.urls import reverse
import json
import os
from datetime import datetime, timedelta

from core.import_models import ImportHistory
from products.excel import ProductExcelImport
from products.custom_excel import StockAdjustmentExcelImporter
from orders.excel import OrderExcelImport


class ImportHistoryListView(LoginRequiredMixin, ListView):
    """Import geçmişi listesi"""
    model = ImportHistory
    template_name = 'core/import_history.html'
    context_object_name = 'imports'
    paginate_by = 20
    ordering = '-created_at'
    
    def get_queryset(self):
        """Filtreleme ve arama"""
        queryset = super().get_queryset()
        
        # Arama
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(file_name__icontains=search) |
                Q(module__icontains=search) |
                Q(created_by__username__icontains=search) |
                Q(created_by__first_name__icontains=search) |
                Q(created_by__last_name__icontains=search)
            )
        
        # Modül filtresi
        module = self.request.GET.get('module')
        if module:
            queryset = queryset.filter(module=module)
        
        # Durum filtresi
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Tarih filtresi
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Context verileri ekle"""
        context = super().get_context_data(**kwargs)
        
        # Filtre değerleri
        context['search'] = self.request.GET.get('search', '')
        context['module'] = self.request.GET.get('module', '')
        context['status'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        # Modül seçenekleri
        context['modules'] = ImportHistory.objects.values_list('module', flat=True).distinct()
        
        # İstatistikler
        context['total_imports'] = ImportHistory.objects.count()
        context['successful_imports'] = ImportHistory.objects.filter(status='completed').count()
        context['failed_imports'] = ImportHistory.objects.filter(status='failed').count()
        context['today_imports'] = ImportHistory.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        return context


class ImportHistoryDetailView(LoginRequiredMixin, DetailView):
    """Import detay görünümü"""
    model = ImportHistory
    template_name = 'core/import_detail.html'
    context_object_name = 'import_history'
    
    def get_context_data(self, **kwargs):
        """Context verileri ekle"""
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        
        # Log dosyasını oku
        if obj.log_file and default_storage.exists(obj.log_file):
            with default_storage.open(obj.log_file, 'r') as f:
                context['log_content'] = f.read()
        
        # İlgili kayıtlar
        if obj.module == 'products':
            from products.models import Product
            if obj.success_details and obj.success_details.get('rows'):
                created_ids = []
                for row_data in obj.success_details['rows'].values():
                    if 'created_id' in row_data:
                        created_ids.append(row_data['created_id'])
                if created_ids:
                    context['related_products'] = Product.objects.filter(
                        id__in=created_ids
                    )[:5]
        elif obj.module == 'orders':
            from orders.models import Order
            if obj.success_details and obj.success_details.get('rows'):
                created_ids = []
                for row_data in obj.success_details['rows'].values():
                    if 'created_id' in row_data:
                        created_ids.append(row_data['created_id'])
                if created_ids:
                    context['related_orders'] = Order.objects.filter(
                        id__in=created_ids
                    )[:5]
                
        return context


class ImportReloadView(LoginRequiredMixin, View):
    """Import dosyasını yeniden yükleme"""
    
    def post(self, request, pk):
        """Import'u yeniden yükle"""
        import_history = get_object_or_404(ImportHistory, pk=pk)
        
        # Dosya kontrolü
        if not import_history.file_path or not default_storage.exists(import_history.file_path):
            messages.error(request, 'Import dosyası bulunamadı.')
            return redirect('core:import-history-detail', pk=pk)
        
        # Yeni import geçmişi oluştur
        new_import = ImportHistory.objects.create(
            module=import_history.module,
            file_name=f"YENIDEN_{import_history.file_name}",
            file_path=import_history.file_path,
            import_params=import_history.import_params,
            status='processing',
            created_by=request.user,
            parent_import=import_history
        )
        
        try:
            # İlgili modülün import işlemini başlat
            if import_history.module == 'products':
                importer = ProductExcelImport()
                with default_storage.open(import_history.file_path, 'rb') as f:
                    result = importer.import_data(f)
                    
            elif import_history.module == 'stock_adjustment':
                importer = StockAdjustmentExcelImporter()
                with default_storage.open(import_history.file_path, 'rb') as f:
                    result = importer.import_file(f)
                    
            elif import_history.module == 'orders':
                importer = OrderExcelImport()
                with default_storage.open(import_history.file_path, 'rb') as f:
                    result = importer.import_data(f)
            else:
                raise ValueError(f'Bilinmeyen modül: {import_history.module}')
            
            # Sonuçları güncelle
            new_import.status = 'completed'
            new_import.total_count = result.total_records
            new_import.success_count = result.created_count + result.updated_count  
            new_import.error_count = result.failed_count
            new_import.processed_count = result.total_records
            new_import.success_details = result.to_dict()
            new_import.completed_at = timezone.now()
            new_import.save()
            
            messages.success(
                request, 
                f'Import başarıyla yeniden yüklendi. '
                f'{result.created_count} kayıt oluşturuldu, '
                f'{result.updated_count} kayıt güncellendi.'
            )
            
        except Exception as e:
            new_import.status = 'failed'
            new_import.error_details = {'general_error': str(e)}
            new_import.completed_at = timezone.now()
            new_import.save()
            
            messages.error(request, f'Import yeniden yüklenemedi: {str(e)}')
        
        return redirect('core:import-history-detail', pk=new_import.pk)


@login_required
def import_file_preview(request, pk):
    """Import dosyasını önizleme"""
    import_history = get_object_or_404(ImportHistory, pk=pk)
    
    if not import_history.file_path or not default_storage.exists(import_history.file_path):
        return JsonResponse({'error': 'Dosya bulunamadı'}, status=404)
    
    try:
        import pandas as pd
        
        # Dosyayı oku
        with default_storage.open(import_history.file_path, 'rb') as f:
            df = pd.read_excel(f, nrows=20)  # İlk 20 satır
        
        # JSON formatına çevir
        data = {
            'columns': df.columns.tolist(),
            'rows': df.values.tolist(),
            'total_rows': len(df)
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def import_download(request, pk):
    """Import dosyasını indir"""
    import_history = get_object_or_404(ImportHistory, pk=pk)
    
    if not import_history.file_path or not default_storage.exists(import_history.file_path):
        messages.error(request, 'Dosya bulunamadı.')
        return redirect('core:import-history-detail', pk=pk)
    
    # Dosyayı indir
    with default_storage.open(import_history.file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{import_history.file_name}"'
        return response


@login_required
def import_status_api(request, pk):
    """Import durumu kontrolü API"""
    import_history = get_object_or_404(ImportHistory, pk=pk)
    
    return JsonResponse({
        'id': import_history.id,
        'status': import_history.status,
        'progress': import_history.get_progress_percentage(),
        'total_count': import_history.total_count,
        'processed_count': import_history.processed_count,
        'success_count': import_history.success_count,
        'error_count': import_history.error_count
    })


@login_required
def import_stats_api(request):
    """Import istatistikleri API"""
    # Son 30 günlük istatistikler
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    stats = {
        'daily': [],
        'by_module': {},
        'by_status': {},
        'recent': []
    }
    
    # Günlük istatistikler
    imports = ImportHistory.objects.filter(created_at__gte=thirty_days_ago)
    for day in range(30):
        date = timezone.now().date() - timedelta(days=day)
        count = imports.filter(created_at__date=date).count()
        stats['daily'].append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Modül bazında
    for module in ImportHistory.objects.values_list('module', flat=True).distinct():
        stats['by_module'][module] = imports.filter(module=module).count()
    
    # Durum bazında
    for status in ['processing', 'completed', 'failed']:
        stats['by_status'][status] = imports.filter(status=status).count()
    
    # Son importlar
    recent = ImportHistory.objects.order_by('-created_at')[:5]
    for imp in recent:
        stats['recent'].append({
            'id': imp.id,
            'filename': imp.file_name,
            'module': imp.module,
            'status': imp.status,
            'created_at': imp.created_at.strftime('%Y-%m-%d %H:%M'),
            'created_by': imp.created_by.get_full_name() or imp.created_by.username
        })
    
    return JsonResponse(stats)