"""
Orders modülü Excel view'ları.
Tüm Excel import/export işlemleri için tek giriş noktası.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.generic import FormView, TemplateView, View
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.http import require_POST
import logging
import uuid
import os
import tempfile

from ..models import Order
from ..forms import ExcelImportForm, OrderFilterForm
from ..excel import OrderExcelManager
from core.excel.exceptions import ExcelError

logger = logging.getLogger(__name__)


class OrderExcelView:
    """
    Excel işlemleri için base view class.
    Diğer Excel view'ları bu sınıfı extend eder.
    """
    model = Order
    permission_required = None  # Alt sınıflar belirler
    
    def __init__(self):
        self.excel_manager = OrderExcelManager()


class OrderExcelImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView, OrderExcelView):
    """Sipariş Excel import view'ı"""
    template_name = 'orders/excel_import.html'
    form_class = ExcelImportForm
    permission_required = 'orders.add_order'
    success_url = None
    
    def get_success_url(self):
        """Import sonuçları sayfasına yönlendir"""
        return reverse('orders:excel-import-results', 
                      kwargs={'session_id': self.session_id})
    
    def form_valid(self, form):
        """Excel dosyasını yükle ve import et"""
        excel_file = form.cleaned_data['excel_file']
        update_existing = form.cleaned_data.get('update_existing', False)
        
        # Session ID oluştur (progress tracking için)
        self.session_id = str(uuid.uuid4())
        
        try:
            # Dosyayı geçici olarak kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Excel manager ile import
            excel_manager = OrderExcelManager()
            results = excel_manager.import_orders_excel(
                tmp_file_path,
                update_existing=update_existing,
                user=self.request.user
            )
            
            # İmportu Celery task olarak çalıştır (opsiyonel)
            if form.cleaned_data.get('async_import', False):
                from ..tasks_excel import import_orders_async
                task = import_orders_async.delay(
                    tmp_file_path, 
                    self.session_id,
                    self.request.user.id,
                    update_existing
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
                f"{results['created']} sipariş oluşturuldu, {results['updated']} sipariş güncellendi."
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
            return redirect('orders:excel-import')
        except Exception as e:
            logger.error(f'Import hatası: {str(e)}')
            messages.error(self.request, 'Beklenmeyen bir hata oluştu.')
            return redirect('orders:excel-import')
        finally:
            # Geçici dosyayı sil
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass


class OrderExcelImportResultsView(LoginRequiredMixin, TemplateView):
    """Import sonuçlarını göster"""
    template_name = 'orders/excel_import_results.html'
    
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
                context['statistics'] = OrderExcelManager().get_import_statistics(results)
            context['session_id'] = session_id
        
        return context


class OrderExcelTemplateView(LoginRequiredMixin, View, OrderExcelView):
    """Import için boş Excel template indir"""
    
    def get(self, request, *args, **kwargs):
        try:
            excel_manager = OrderExcelManager()
            template_content = excel_manager.generate_order_template()
            
            response = HttpResponse(
                template_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            filename = f'siparis_import_template_{timezone.now().strftime("%Y%m%d")}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f'Template oluşturma hatası: {str(e)}')
            messages.error(request, 'Template oluşturulurken bir hata oluştu.')
            return redirect('orders:excel-import')


class OrderExcelReportView(LoginRequiredMixin, PermissionRequiredMixin, View, OrderExcelView):
    """Sipariş raporları oluştur"""
    permission_required = 'orders.view_order'
    
    def get(self, request, *args, **kwargs):
        try:
            # Filtre parametrelerini al
            filter_form = OrderFilterForm(request.GET)
            queryset = self._get_filtered_queryset(filter_form)
            
            # Rapor tipini al
            report_type = request.GET.get('type', 'summary')
            
            # Excel manager ile rapor oluştur
            excel_manager = OrderExcelManager()
            report_content = excel_manager.generate_order_report(
                queryset,
                start_date=filter_form.cleaned_data.get('start_date') if filter_form.is_valid() else None,
                end_date=filter_form.cleaned_data.get('end_date') if filter_form.is_valid() else None,
                report_type=report_type
            )
            
            # Response oluştur
            filename = f'siparis_raporu_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            response = HttpResponse(
                report_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f'Rapor oluşturma hatası: {str(e)}')
            messages.error(request, 'Rapor oluşturulurken bir hata oluştu.')
            return redirect('orders:order-list')
    
    def _get_filtered_queryset(self, filter_form):
        """Form'a göre queryset filtrele"""
        queryset = Order.objects.all()
        
        if filter_form.is_valid():
            # Tarih aralığı
            if filter_form.cleaned_data.get('start_date'):
                queryset = queryset.filter(
                    order_date__gte=filter_form.cleaned_data['start_date']
                )
                
            if filter_form.cleaned_data.get('end_date'):
                queryset = queryset.filter(
                    order_date__lte=filter_form.cleaned_data['end_date']
                )
                
            # Müşteriye göre filtrele
            if filter_form.cleaned_data.get('customer'):
                queryset = queryset.filter(
                    customer=filter_form.cleaned_data['customer']
                )
                
            # Duruma göre filtrele
            if filter_form.cleaned_data.get('status'):
                queryset = queryset.filter(
                    status=filter_form.cleaned_data['status']
                )
                
            # Ödeme durumuna göre filtrele
            if filter_form.cleaned_data.get('payment_status'):
                queryset = queryset.filter(
                    payment_status=filter_form.cleaned_data['payment_status']
                )
                
            # Segmente göre filtrele
            if filter_form.cleaned_data.get('segment'):
                queryset = queryset.filter(
                    segment=filter_form.cleaned_data['segment']
                )
                
            # Sorumluya göre filtrele
            if filter_form.cleaned_data.get('owner'):
                queryset = queryset.filter(
                    owner=filter_form.cleaned_data['owner']
                )
                
            # Minimum tutara göre filtrele
            if filter_form.cleaned_data.get('min_amount'):
                queryset = queryset.filter(
                    total_amount__gte=filter_form.cleaned_data['min_amount']
                )
                
            # Maksimum tutara göre filtrele
            if filter_form.cleaned_data.get('max_amount'):
                queryset = queryset.filter(
                    total_amount__lte=filter_form.cleaned_data['max_amount']
                )
                
        # İlişkili verileri prefetch et
        queryset = queryset.select_related('customer', 'owner', 'billing_address', 'shipping_address')
        
        return queryset


# Function-based views (geriye uyumluluk için)
@login_required
@permission_required('orders.add_order')
def order_excel_import_view(request):
    """Function-based import view"""
    view = OrderExcelImportView.as_view()
    return view(request)


@login_required
def order_excel_import_results_view(request, session_id):
    """Function-based import results view"""
    view = OrderExcelImportResultsView.as_view()
    return view(request, session_id=session_id)


@login_required
def order_excel_template_view(request):
    """Function-based template view"""
    view = OrderExcelTemplateView.as_view()
    return view(request)


@login_required
@permission_required('orders.view_order')
def order_excel_report_view(request):
    """Function-based report view"""
    view = OrderExcelReportView.as_view()
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
        
        # Excel dosyasını oku
        import pandas as pd
        df = pd.read_excel(tmp_file_path)
        
        # Gerekli sütunları kontrol et
        required_columns = ["SIPARIŞ TARIHI VE SAATI", "SIPARIŞ NO", "MÜŞTERI ISMI", "SKU", "ÜRÜN ISMI", "ADET", "BIRIM FIYAT"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        # Sonuç oluştur
        validation_result = {
            'valid': len(missing_columns) == 0,
            'total_rows': len(df),
            'file_size': os.path.getsize(tmp_file_path),
            'orders_count': df["SIPARIŞ NO"].nunique() if "SIPARIŞ NO" in df.columns else 0,
        }
        
        if missing_columns:
            validation_result['errors'] = [f"Eksik sütunlar: {', '.join(missing_columns)}"]
        
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