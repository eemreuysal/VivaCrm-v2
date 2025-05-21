"""
Excel işlemleri için facade pattern implementasyonu.
Tüm Excel import/export işlemleri için tek bir giriş noktası sağlar.
"""
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
import tempfile
import uuid
import os
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from ..models import Product, Category, ProductFamily
from ..excel.manager import ProductExcelManager

logger = logging.getLogger(__name__)


class ExcelImportFacade:
    """
    Excel import işlemleri için facade sınıfı.
    View'lar ile Excel manager arasında köprü görevi görür.
    """
    
    def __init__(self, request=None):
        """
        Facade initialize
        
        Args:
            request: HTTP request objesi (opsiyonel)
        """
        self.request = request
        self.excel_manager = ProductExcelManager()
        self.session_id = None
    
    def handle_import_form(self, form, redirect_url=None):
        """
        Excel import form'unu işle
        
        Args:
            form: Doldurulmuş ve doğrulanmış form
            redirect_url: Başarılı import sonrası yönlendirilecek URL
            
        Returns:
            HttpResponse: Yönlendirme yanıtı
            
        Raises:
            Exception: Import sırasında oluşan hatalar
        """
        if not form.is_valid():
            return self._handle_form_errors(form)
        
        # Form verileri
        excel_file = form.cleaned_data['excel_file']
        use_chunks = form.cleaned_data.get('use_chunks', False)
        skip_validation = form.cleaned_data.get('skip_validation', False)
        async_import = form.cleaned_data.get('async_import', False)
        
        # Session ID oluştur (progress tracking için)
        self.session_id = str(uuid.uuid4())
        
        try:
            # Dosyayı geçici olarak kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Asenkron import
            if async_import:
                return self._start_async_import(tmp_file_path, redirect_url)
                
            # Senkron import
            return self._perform_import(
                tmp_file_path, 
                use_chunks=use_chunks,
                skip_validation=skip_validation,
                redirect_url=redirect_url
            )
        except Exception as e:
            logger.error(f"Import hatası: {str(e)}")
            if self.request:
                messages.error(self.request, f"Import hatası: {str(e)}")
            
            # Hata durumunda orijinal sayfaya yönlendir
            return redirect(redirect_url or 'products:excel-import') 
        finally:
            # Geçici dosyayı temizle
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    logger.warning(f"Geçici dosya silinemedi: {str(e)}")
    
    def _handle_form_errors(self, form):
        """Form hatalarını işle"""
        if self.request:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
        
        return redirect('products:excel-import')
    
    def _start_async_import(self, file_path, redirect_url=None):
        """Asenkron import işlemini başlat"""
        try:
            # Celery task'ı başlat
            from ..tasks_excel import import_products_async
            
            task = import_products_async.delay(
                file_path, 
                self.session_id,
                self.request.user.id if self.request else None
            )
            
            # Task bilgisini cache'de sakla
            cache.set(f'import_task_{self.session_id}', task.id, 3600)
            
            # İlerleme bilgisini başlat
            cache.set(f'import_progress_{self.session_id}', {
                'status': 'started',
                'message': 'Import başlatıldı, işlem devam ediyor...',
                'progress': 0
            }, 3600)
            
            if self.request:
                messages.info(
                    self.request, 
                    f"Import işlemi arkaplanda başlatıldı. İşlem ID: {self.session_id}"
                )
            
            # Sonuç sayfasına yönlendir
            return redirect(self._get_results_url(redirect_url))
            
        except Exception as e:
            logger.error(f"Asenkron import başlatılamadı: {str(e)}")
            if self.request:
                messages.error(self.request, f"İşlem başlatılamadı: {str(e)}")
            return redirect('products:excel-import')
    
    def _perform_import(self, file_path, use_chunks=False, skip_validation=False, redirect_url=None):
        """Excel import işlemini gerçekleştir"""
        try:
            # Excel manager ile import
            results = self.excel_manager.import_products(
                file_path,
                use_chunks=use_chunks,
                skip_validation=skip_validation,
                user_id=self.request.user.id if self.request else None
            )
            
            # Sonuçları cache'e kaydet
            cache.set(f'import_results_{self.session_id}', results, 3600)
            
            # Başarı mesajı
            if self.request:
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
            return redirect(self._get_results_url(redirect_url))
            
        except Exception as e:
            logger.error(f"Import hatası: {str(e)}")
            if self.request:
                messages.error(self.request, f"Import hatası: {str(e)}")
            return redirect('products:excel-import')
    
    def _get_results_url(self, redirect_url=None):
        """Sonuç sayfası URL'sini oluştur"""
        if redirect_url:
            return f"{redirect_url}?session_id={self.session_id}"
        else:
            return reverse('products:excel-import-results', kwargs={'session_id': self.session_id})
    
    def get_import_results(self, session_id):
        """Import sonuçlarını al"""
        # Cache'den sonuçları kontrol et
        results = cache.get(f'import_results_{session_id}')
        
        # Task durumunu kontrol et
        task_id = cache.get(f'import_task_{session_id}')
        task_info = None
        
        if task_id:
            from celery.result import AsyncResult
            task_result = AsyncResult(task_id)
            task_info = {
                'id': task_id,
                'status': task_result.status,
                'ready': task_result.ready(),
                'result': task_result.result if task_result.ready() else None
            }
            
            # Task tamamlandıysa sonuçları güncelle
            if task_result.ready() and task_result.successful() and task_result.result:
                results = task_result.result
                
        return {
            'results': results,
            'task': task_info,
            'session_id': session_id,
            'statistics': self.get_import_statistics(results) if results else None
        }
    
    def get_import_statistics(self, results):
        """Import istatistiklerini hesapla"""
        if not results:
            return None
            
        return self.excel_manager.get_import_statistics(results)
    
    def validate_excel_file(self, excel_file):
        """Excel dosyasını doğrula"""
        try:
            # Dosyayı geçici olarak kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Excel manager ile validate
            validation_result = self.excel_manager.validate_import_file(tmp_file_path)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Validasyon hatası: {str(e)}")
            return {
                'valid': False,
                'errors': [str(e)]
            }
        finally:
            # Geçici dosyayı temizle
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass


class ExcelExportFacade:
    """
    Excel export işlemleri için facade sınıfı.
    View'lar ile Excel manager arasında köprü görevi görür.
    """
    
    def __init__(self, request=None):
        """
        Facade initialize
        
        Args:
            request: HTTP request objesi (opsiyonel)
        """
        self.request = request
        self.excel_manager = ProductExcelManager()
    
    def export_products(self, queryset, export_type='full', use_chunks=False):
        """
        Ürünleri Excel'e export et
        
        Args:
            queryset: Export edilecek ürünler queryset'i
            export_type: Export tipi ('full', 'price_list', 'inventory', 'stock_info')
            use_chunks: Büyük veri setleri için chunk kullan
            
        Returns:
            HttpResponse: Excel dosyası içeren HTTP yanıtı
        """
        try:
            # Export işlemi
            excel_content = self.excel_manager.export_products(
                queryset,
                export_type=export_type,
                use_chunks=use_chunks or queryset.count() > 5000
            )
            
            # Response oluştur
            response = HttpResponse(
                excel_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Dosya adı
            filename = self._generate_export_filename(export_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Export hatası: {str(e)}")
            if self.request:
                messages.error(self.request, f"Export hatası: {str(e)}")
            return redirect('products:product-list')
    
    def generate_template(self):
        """
        Import için Excel template oluştur
        
        Returns:
            HttpResponse: Excel template dosyası içeren HTTP yanıtı
        """
        try:
            # Template oluştur
            template_content = self.excel_manager.generate_import_template()
            
            # Response oluştur
            response = HttpResponse(
                template_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Dosya adı
            filename = f'urun_import_template_{timezone.now().strftime("%Y%m%d")}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Template oluşturma hatası: {str(e)}")
            if self.request:
                messages.error(self.request, f"Template oluşturma hatası: {str(e)}")
            return redirect('products:excel-import')
    
    def _generate_export_filename(self, export_type):
        """Export dosya adı oluştur"""
        type_names = {
            'full': 'tam',
            'price_list': 'fiyat_listesi',
            'inventory': 'envanter',
            'stock_info': 'stok_bilgisi'
        }
        type_name = type_names.get(export_type, export_type)
        
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        return f'urunler_{type_name}_{timestamp}.xlsx'