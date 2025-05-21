"""
Products Excel Celery task'ları - Refactored version.
Asenkron Excel işlemleri için.
"""
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
import logging
from pathlib import Path

from .excel.manager import ProductExcelManager
from .models import Product
from core.excel.exceptions import ExcelError

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def import_products_async(self, file_path: str, session_id: str, user_id: int = None):
    """
    Ürünleri asenkron olarak import et.
    Büyük dosyalar için Celery task.
    """
    task_id = self.request.id
    
    # İlerleme takibi için cache key'leri
    progress_key = f'import_progress_{session_id}'
    result_key = f'import_results_{session_id}'
    
    # Başlangıç ilerleme durumu
    cache.set(progress_key, {
        'status': 'processing',
        'total': 0,
        'processed': 0,
        'success': 0,
        'errors': 0,
        'percent': 0,
        'message': 'Import başlatılıyor...',
        'task_id': task_id,
        'started_at': timezone.now().isoformat()
    }, timeout=3600)
    
    try:
        # Excel manager
        manager = ProductExcelManager()
        
        # Progress callback
        def update_progress(current, total, message=''):
            percent = int((current / total) * 100) if total > 0 else 0
            cache.set(progress_key, {
                'status': 'processing',
                'total': total,
                'processed': current,
                'percent': percent,
                'message': message or f'İşleniyor... {current}/{total}',
                'task_id': task_id
            }, timeout=3600)
        
        # Import işlemi
        file_path = Path(file_path)
        results = manager.import_products(
            file_path,
            use_chunks=True,
            progress_callback=update_progress,
            user_id=user_id
        )
        
        # Sonuçları cache'e kaydet
        cache.set(result_key, results, timeout=3600)
        
        # Final ilerleme durumu
        cache.set(progress_key, {
            'status': 'completed',
            'total': results['total_rows'],
            'processed': results['total_rows'],
            'success': results['success_count'],
            'errors': results['error_count'],
            'percent': 100,
            'message': 'Import tamamlandı',
            'task_id': task_id,
            'completed_at': timezone.now().isoformat(),
            'results': results
        }, timeout=3600)
        
        logger.info(f"Import tamamlandı: {results['success_count']} başarılı, {results['error_count']} hatalı")
        
        return {
            'session_id': session_id,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Import hatası: {str(e)}")
        
        # Hata durumu
        cache.set(progress_key, {
            'status': 'failed',
            'error': str(e),
            'message': 'Import başarısız oldu',
            'task_id': task_id,
            'failed_at': timezone.now().isoformat()
        }, timeout=3600)
        
        raise
    finally:
        # Geçici dosyayı temizle
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
        except Exception as e:
            logger.warning(f"Geçici dosya silinemedi: {e}")


@shared_task(bind=True)
def export_products_async(self, queryset_ids: list, export_type: str, session_id: str, user_id: int = None):
    """
    Ürünleri asenkron olarak export et.
    Büyük veri setleri için Celery task.
    """
    task_id = self.request.id
    
    # İlerleme takibi
    progress_key = f'export_progress_{session_id}'
    result_key = f'export_result_{session_id}'
    
    # Başlangıç durumu
    cache.set(progress_key, {
        'status': 'processing',
        'total': len(queryset_ids),
        'processed': 0,
        'percent': 0,
        'message': 'Export başlatılıyor...',
        'task_id': task_id,
        'started_at': timezone.now().isoformat()
    }, timeout=3600)
    
    try:
        # QuerySet'i yeniden oluştur
        queryset = Product.objects.filter(id__in=queryset_ids)
        
        # Excel manager
        manager = ProductExcelManager()
        
        # Progress callback
        def update_progress(current, total, message=''):
            percent = int((current / total) * 100) if total > 0 else 0
            cache.set(progress_key, {
                'status': 'processing',
                'total': total,
                'processed': current,
                'percent': percent,
                'message': message or f'Export ediliyor... {current}/{total}',
                'task_id': task_id
            }, timeout=3600)
        
        # Export işlemi
        excel_content = manager.export_products(
            queryset,
            export_type=export_type,
            use_chunks=True,
            progress_callback=update_progress
        )
        
        # Dosyayı kaydet
        from django.core.files.base import ContentFile
        file_name = f'export_{export_type}_{session_id}.xlsx'
        
        # Media dizinine kaydet
        from django.core.files.storage import default_storage
        file_path = default_storage.save(f'exports/{file_name}', ContentFile(excel_content))
        file_url = default_storage.url(file_path)
        
        # Sonuç
        result = {
            'file_url': file_url,
            'file_name': file_name,
            'file_size': len(excel_content),
            'row_count': queryset.count(),
            'export_type': export_type
        }
        
        cache.set(result_key, result, timeout=3600)
        
        # Final durum
        cache.set(progress_key, {
            'status': 'completed',
            'total': queryset.count(),
            'processed': queryset.count(),
            'percent': 100,
            'message': 'Export tamamlandı',
            'task_id': task_id,
            'completed_at': timezone.now().isoformat(),
            'result': result
        }, timeout=3600)
        
        logger.info(f"Export tamamlandı: {file_name}")
        
        return {
            'session_id': session_id,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Export hatası: {str(e)}")
        
        # Hata durumu
        cache.set(progress_key, {
            'status': 'failed',
            'error': str(e),
            'message': 'Export başarısız oldu',
            'task_id': task_id,
            'failed_at': timezone.now().isoformat()
        }, timeout=3600)
        
        raise


@shared_task
def cleanup_old_exports():
    """
    Eski export dosyalarını temizle.
    Günlük çalışacak periodic task.
    """
    from django.core.files.storage import default_storage
    from datetime import timedelta
    
    try:
        # 7 günden eski dosyaları sil
        cutoff_date = timezone.now() - timedelta(days=7)
        
        # Export dizinindeki dosyaları listele
        export_dir = 'exports/'
        if default_storage.exists(export_dir):
            files = default_storage.listdir(export_dir)[1]  # Sadece dosyalar
            
            deleted_count = 0
            for file_name in files:
                file_path = f'{export_dir}{file_name}'
                
                # Dosya yaşını kontrol et
                modified_time = default_storage.get_modified_time(file_path)
                if modified_time < cutoff_date:
                    default_storage.delete(file_path)
                    deleted_count += 1
                    logger.info(f"Eski export silindi: {file_path}")
            
            logger.info(f"Toplam {deleted_count} eski export dosyası silindi")
            return deleted_count
            
    except Exception as e:
        logger.error(f"Export temizleme hatası: {str(e)}")
        raise


@shared_task
def validate_product_data():
    """
    Ürün verilerini doğrula ve tutarsızlıkları raporla.
    Haftalık çalışacak periodic task.
    """
    from .models import Product, Category, ProductFamily
    
    issues = []
    
    try:
        # Kategorisiz ürünler
        products_without_category = Product.objects.filter(category__isnull=True)
        if products_without_category.exists():
            issues.append({
                'type': 'missing_category',
                'count': products_without_category.count(),
                'product_ids': list(products_without_category.values_list('id', flat=True)[:10])
            })
        
        # Negatif stoklu ürünler
        negative_stock_products = Product.objects.filter(current_stock__lt=0)
        if negative_stock_products.exists():
            issues.append({
                'type': 'negative_stock',
                'count': negative_stock_products.count(),
                'product_ids': list(negative_stock_products.values_list('id', flat=True)[:10])
            })
        
        # Geçersiz fiyatlı ürünler
        invalid_price_products = Product.objects.filter(
            models.Q(price__lte=0) | models.Q(price__isnull=True)
        )
        if invalid_price_products.exists():
            issues.append({
                'type': 'invalid_price',
                'count': invalid_price_products.count(),
                'product_ids': list(invalid_price_products.values_list('id', flat=True)[:10])
            })
        
        # İndirimli fiyat > normal fiyat
        invalid_sale_products = Product.objects.filter(
            sale_price__gt=models.F('price')
        )
        if invalid_sale_products.exists():
            issues.append({
                'type': 'invalid_sale_price',
                'count': invalid_sale_products.count(),
                'product_ids': list(invalid_sale_products.values_list('id', flat=True)[:10])
            })
        
        # Raporu kaydet
        if issues:
            report = {
                'date': timezone.now().isoformat(),
                'issues': issues,
                'total_products': Product.objects.count()
            }
            
            # Cache'e kaydet veya e-posta gönder
            cache.set('product_validation_report', report, timeout=86400)  # 1 gün
            
            logger.warning(f"Ürün doğrulama tamamlandı: {len(issues)} sorun bulundu")
        else:
            logger.info("Ürün doğrulama tamamlandı: Sorun bulunamadı")
        
        return issues
        
    except Exception as e:
        logger.error(f"Ürün doğrulama hatası: {str(e)}")
        raise