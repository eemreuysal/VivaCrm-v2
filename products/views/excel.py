"""
Products modülü Excel view'ları.
Tüm Excel import/export işlemleri için tek giriş noktası.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.generic import FormView, TemplateView, View
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.http import require_POST
from django.db.models import Q
import logging
import uuid
import os
import tempfile

from ..models import Product, Category, ProductFamily
from ..forms import ProductFilterForm, ExcelImportForm
from ..excel.manager import ProductExcelManager
from core.excel.exceptions import ExcelError

logger = logging.getLogger(__name__)


class ProductExcelView:
    """
    Excel işlemleri için base view class.
    Diğer Excel view'ları bu sınıfı extend eder.
    """
    model = Product
    permission_required = None  # Alt sınıflar belirler
    
    def __init__(self):
        self.excel_manager = ProductExcelManager()


class ProductExcelImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Ürün Excel import view'ı"""
    template_name = 'products/excel_import.html'
    form_class = ExcelImportForm
    permission_required = 'products.add_product'
    success_url = None
    
    def get_success_url(self):
        """Import sonuçları sayfasına yönlendir"""
        return reverse('products:excel-import-results', 
                      kwargs={'session_id': self.session_id})
    
    def form_valid(self, form):
        """Excel dosyasını yükle ve import et"""
        excel_file = form.cleaned_data['excel_file']
        
        # Session ID oluştur (progress tracking için)
        self.session_id = str(uuid.uuid4())
        
        try:
            # Dosyayı geçici olarak kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Excel manager ile import
            use_chunks = form.cleaned_data.get('use_chunks', False)
            skip_validation = form.cleaned_data.get('skip_validation', False)
            
            excel_manager = ProductExcelManager()
            results = excel_manager.import_products(
                tmp_file_path,
                use_chunks=use_chunks,
                skip_validation=skip_validation,
                user_id=self.request.user.id
            )
            
            # İmportu Celery task olarak çalıştır (opsiyonel)
            if form.cleaned_data.get('async_import', False):
                from ..tasks_excel_new import import_products_async
                task = import_products_async.delay(
                    tmp_file_path, 
                    self.session_id,
                    self.request.user.id
                )
                messages.info(self.request, 
                             f"Import işlemi arkaplanda başlatıldı. Task ID: {task.id}")
                cache.set(f'import_task_{self.session_id}', task.id, 3600)
                return redirect(self.get_success_url())
            
            # Sonuçları cache'e kaydet
            cache.set(f'import_results_{self.session_id}', results, 3600)
            
            # Başarı mesajı
            messages.success(
                self.request,
                f"{results['success_count']} ürün başarıyla import edildi."
            )
            
            if results['error_count'] > 0:
                messages.warning(
                    self.request,
                    f"{results['error_count']} satırda hata oluştu."
                )
            
            # Sonuç sayfasına yönlendir
            return redirect(self.get_success_url())
            
        except ExcelError as e:
            messages.error(self.request, f'Excel hatası: {str(e)}')
            return redirect('products:excel-import')
        except Exception as e:
            logger.error(f'Import hatası: {str(e)}')
            messages.error(self.request, 'Beklenmeyen bir hata oluştu.')
            return redirect('products:excel-import')
        finally:
            # Geçici dosyayı sil
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                    

class ProductExcelImportResultsView(LoginRequiredMixin, TemplateView):
    """Import sonuçlarını göster"""
    template_name = 'products/excel_import_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get('session_id')
        
        # Cache'den sonuçları al
        results = cache.get(f'import_results_{session_id}')
        
        # Eğer asenkron task çalışıyorsa, durumunu kontrol et
        task_id = cache.get(f'import_task_{session_id}')
        if task_id:
            from celery.result import AsyncResult
            task_result = AsyncResult(task_id)
            context['task'] = {
                'id': task_id,
                'status': task_result.status,
                'ready': task_result.ready(),
                'result': task_result.result if task_result.ready() else None
            }
        
        if not results and not task_id:
            context['error'] = 'Sonuçlar bulunamadı veya süresi doldu.'
        else:
            context['results'] = results
            if results:
                context['statistics'] = ProductExcelManager().get_import_statistics(results)
            context['session_id'] = session_id
        
        return context


class ProductExcelExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Ürünleri Excel'e export et"""
    permission_required = 'products.view_product'
    
    def get(self, request, *args, **kwargs):
        try:
            # Filtre parametrelerini al
            filter_form = ProductFilterForm(request.GET)
            queryset = self.get_filtered_queryset(filter_form)
            
            # Export tipini al
            export_type = request.GET.get('type', 'full')
            
            # Excel manager ile export
            excel_manager = ProductExcelManager()
            excel_content = excel_manager.export_products(
                queryset,
                export_type=export_type,
                use_chunks=queryset.count() > 5000  # Büyük veri setleri için
            )
            
            # Response oluştur
            return self.create_response(excel_content, export_type)
            
        except Exception as e:
            logger.error(f'Export hatası: {str(e)}')
            messages.error(request, 'Export sırasında bir hata oluştu.')
            return redirect('products:product-list')
    
    def get_filtered_queryset(self, filter_form):
        """Form'a göre queryset filtrele"""
        queryset = Product.objects.all()
        
        if filter_form.is_valid():
            # Kategori filtresi
            if filter_form.cleaned_data.get('category'):
                queryset = queryset.filter(
                    category=filter_form.cleaned_data['category']
                )
                
            # Durum filtresi
            if filter_form.cleaned_data.get('status'):
                queryset = queryset.filter(
                    status=filter_form.cleaned_data['status']
                )
                
            # Arama filtresi
            if filter_form.cleaned_data.get('search'):
                search_term = filter_form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(code__icontains=search_term) |
                    Q(sku__icontains=search_term)
                )
                
            # Fiyat aralığı
            if filter_form.cleaned_data.get('min_price'):
                queryset = queryset.filter(
                    price__gte=filter_form.cleaned_data['min_price']
                )
                
            if filter_form.cleaned_data.get('max_price'):
                queryset = queryset.filter(
                    price__lte=filter_form.cleaned_data['max_price']
                )
                
            # Stok filtresi
            if filter_form.cleaned_data.get('in_stock'):
                queryset = queryset.filter(current_stock__gt=0)
            
        return queryset
        
    def create_response(self, excel_content, export_type):
        """Excel response oluştur"""
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Dosya adı
        type_names = {
            'full': 'tam',
            'price_list': 'fiyat_listesi',
            'inventory': 'envanter',
            'stock_info': 'stok_bilgisi'
        }
        type_name = type_names.get(export_type, export_type)
        
        filename = f'urunler_{type_name}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


class ProductExcelTemplateView(LoginRequiredMixin, View):
    """Import için boş Excel template indir"""
    
    def get(self, request, *args, **kwargs):
        try:
            excel_manager = ProductExcelManager()
            template_content = excel_manager.generate_import_template()
            
            response = HttpResponse(
                template_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            filename = f'urun_import_template_{timezone.now().strftime("%Y%m%d")}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f'Template oluşturma hatası: {str(e)}')
            messages.error(request, 'Template oluşturulurken bir hata oluştu.')
            return redirect('products:excel-import')


# Function-based views (geriye uyumluluk için)
@login_required
def product_excel_import_view(request):
    """Function-based import view"""
    view = ProductExcelImportView.as_view()
    return view(request)


@login_required
def product_excel_export_view(request):
    """Function-based export view"""
    view = ProductExcelExportView.as_view()
    return view(request)


@login_required
def product_excel_template_view(request):
    """Function-based template view"""
    view = ProductExcelTemplateView.as_view()
    return view(request)


@login_required
@require_POST
def validate_excel_file(request):
    """Excel dosyasını import öncesi doğrula (AJAX)"""
    if 'excel_file' not in request.FILES:
        return JsonResponse({'error': 'Dosya bulunamadı'}, status=400)
    
    excel_file = request.FILES['excel_file']
    
    try:
        # Dosyayı geçici olarak kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            for chunk in excel_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        # Validasyon
        excel_manager = ProductExcelManager()
        validation_result = excel_manager.validate_import_file(tmp_file_path)
        
        return JsonResponse(validation_result)
        
    except Exception as e:
        logger.error(f'Validasyon hatası: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        # Geçici dosyayı sil
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass


@login_required
def import_progress_api(request, session_id):
    """Import işlemi ilerleme durumu (AJAX)"""
    progress_data = cache.get(f'import_progress_{session_id}')
    
    # Asenkron task varsa durumunu kontrol et
    task_id = cache.get(f'import_task_{session_id}')
    if task_id:
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id)
        if task_result.ready() and task_result.successful():
            # Task tamamlandıysa sonuçları al
            progress_data = {
                'status': 'completed',
                'task_id': task_id,
                'result': task_result.result
            }
    
    if not progress_data:
        return JsonResponse({
            'status': 'not_found',
            'message': 'İlerleme bilgisi bulunamadı'
        }, status=404)
    
    return JsonResponse(progress_data)