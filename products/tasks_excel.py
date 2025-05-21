"""
Ürün Excel import/export için Celery task'ları
"""
from celery import shared_task
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
import pandas as pd
import logging
import json
from decimal import Decimal
from typing import Dict, Any, List

from core.models_import import ImportJob, ImportError, ImportHistory
from core.websocket_utils import send_import_progress, send_import_completed, send_import_failed
from .models import Product, Category, ProductFamily, StockMovement
from .excel import (
    validate_category, validate_family, validate_price, validate_date,
    validate_boolean, validate_attribute_value, process_image_url, validate_status
)

logger = logging.getLogger(__name__)

# Chunk size for processing
CHUNK_SIZE = 100


@shared_task(bind=True, name='products.tasks.product_import')
def product_import_task(self, import_job_id: str, file_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ürünleri Excel dosyasından asenkron olarak içe aktarır.
    
    Args:
        import_job_id: Import işlemi ID'si
        file_path: Excel dosyasının yolu
        settings: Import ayarları (update_existing, chunk_size vb.)
    
    Returns:
        Import işlemi sonuç özeti
    """
    try:
        # Import job'ı al
        import_job = ImportJob.objects.get(id=import_job_id)
        import_job.status = 'processing'
        import_job.started_at = timezone.now()
        import_job.save()
        
        # Geçmiş kaydı ekle
        ImportHistory.objects.create(
            import_job=import_job,
            action='İşlem başlatıldı',
            description=f'Ürün import işlemi başlatıldı. Dosya: {file_path}'
        )
        
        # Excel dosyasını oku
        df = pd.read_excel(file_path)
        total_rows = len(df)
        
        import_job.total_rows = total_rows
        import_job.save()
        
        # Alan eşleşmelerini hazırla
        field_mapping = {
            'Product Code *': 'code',
            'Product Code': 'code',
            'Product Name *': 'name',
            'Product Name': 'name',
            'Category *': 'category',
            'Category': 'category',
            'Product Family': 'family',
            'Color': 'color',
            'Size': 'size',
            'Material': 'material',
            'Brand': 'brand',
            'Image URL': 'image_url',
            'Price *': 'price',
            'Price': 'price',
            'Cost': 'cost',
            'Tax Rate (%)': 'tax_rate',
            'Sale Price': 'sale_price',
            'Sale End Date (YYYY-MM-DD)': 'sale_end_date',
            'Initial Stock *': 'current_stock',
            'Current Stock': 'current_stock',
            'Stock Alert Threshold': 'threshold_stock',
            'Physical Product (TRUE/FALSE)': 'is_physical',
            'Weight (kg)': 'weight',
            'Dimensions': 'dimensions',
            'SKU': 'sku',
            'Barcode': 'barcode',
            'Status': 'status',
            'Description': 'description'
        }
        
        # Chunk'lar halinde işle
        chunk_size = settings.get('chunk_size', CHUNK_SIZE)
        total_chunks = (total_rows + chunk_size - 1) // chunk_size
        import_job.total_chunks = total_chunks
        import_job.save()
        
        success_count = 0
        error_count = 0
        update_count = 0
        
        for chunk_num, start_idx in enumerate(range(0, total_rows, chunk_size)):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx]
            
            import_job.current_chunk = chunk_num + 1
            import_job.save()
            
            # Chunk'ı işle
            chunk_result = process_product_chunk(
                chunk=chunk,
                import_job=import_job,
                field_mapping=field_mapping,
                settings=settings,
                start_row=start_idx
            )
            
            success_count += chunk_result['success']
            error_count += chunk_result['errors']
            update_count += chunk_result['updates']
            
            # İlerlemeyi güncelle
            import_job.processed_rows = end_idx
            import_job.success_count = success_count
            import_job.error_count = error_count
            import_job.update_progress()
            
            # Celery task durumunu güncelle
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': import_job.processed_rows,
                    'total': import_job.total_rows,
                    'progress': float(import_job.progress),
                    'success': success_count,
                    'errors': error_count
                }
            )
            
            # WebSocket ile ilerleme güncellemesi gönder
            send_import_progress(import_job_id, {
                'status': import_job.status,
                'progress': float(import_job.progress),
                'processed_rows': import_job.processed_rows,
                'total_rows': import_job.total_rows,
                'success_count': success_count,
                'error_count': error_count,
                'current_chunk': import_job.current_chunk,
                'total_chunks': import_job.total_chunks
            })
        
        # İşlemi tamamla
        import_job.result_summary = {
            'total_rows': total_rows,
            'success_count': success_count,
            'error_count': error_count,
            'update_count': update_count,
            'created_count': success_count - update_count
        }
        import_job.complete()
        
        # Geçmiş kaydı ekle
        ImportHistory.objects.create(
            import_job=import_job,
            action='İşlem tamamlandı',
            description=f'Başarıyla tamamlandı. {success_count} ürün işlendi, {error_count} hata oluştu.',
            metadata=import_job.result_summary
        )
        
        # WebSocket ile tamamlanma bildirimi gönder
        send_import_completed(import_job_id, {
            'status': 'completed',
            'progress': 100,
            'processed_rows': import_job.processed_rows,
            'total_rows': import_job.total_rows,
            'success_count': success_count,
            'error_count': error_count,
            'result_summary': import_job.result_summary
        })
        
        return import_job.result_summary
        
    except Exception as e:
        logger.error(f"Product import task error: {str(e)}")
        
        if 'import_job' in locals():
            import_job.fail(str(e))
            ImportHistory.objects.create(
                import_job=import_job,
                action='İşlem başarısız',
                description=f'Hata: {str(e)}'
            )
            
            # WebSocket ile hata bildirimi gönder
            send_import_failed(import_job_id, {
                'status': 'failed',
                'error_message': str(e),
                'processed_rows': import_job.processed_rows,
                'total_rows': import_job.total_rows,
                'success_count': import_job.success_count,
                'error_count': import_job.error_count
            })
        
        raise


def process_product_chunk(chunk: pd.DataFrame, import_job: ImportJob, 
                         field_mapping: Dict[str, str], settings: Dict[str, Any],
                         start_row: int) -> Dict[str, int]:
    """
    DataFrame chunk'ını işleyip ürünleri içe aktarır.
    
    Returns:
        İşlem sonucu istatistikleri
    """
    success_count = 0
    error_count = 0
    update_count = 0
    update_existing = settings.get('update_existing', True)
    
    # Sütun adlarını eşleştir
    chunk.rename(columns=field_mapping, inplace=True)
    
    for idx, row in chunk.iterrows():
        row_number = start_row + idx + 2  # Excel'de 1-indexed + başlık satırı
        
        try:
            with transaction.atomic():
                # Verileri doğrula ve hazırla
                product_data = prepare_product_data(row)
                
                # Ürünü oluştur veya güncelle
                code = product_data.pop('code')
                existing_product = Product.objects.filter(code=code).first()
                
                if existing_product and update_existing:
                    # Mevcut ürünü güncelle
                    for key, value in product_data.items():
                        setattr(existing_product, key, value)
                    existing_product.save()
                    product = existing_product
                    update_count += 1
                elif existing_product and not update_existing:
                    # Güncelleme yapma, atla
                    ImportError.objects.create(
                        import_job=import_job,
                        row_number=row_number,
                        error_type='duplicate',
                        error_message=f'Ürün kodu {code} zaten mevcut',
                        row_data=row.to_dict()
                    )
                    error_count += 1
                    continue
                else:
                    # Yeni ürün oluştur
                    product = Product.objects.create(code=code, **product_data)
                
                # Özel alanları işle (renkler, boyutlar, resimler vb.)
                process_product_attributes(product, row, import_job, row_number)
                
                # Stok hareketi oluştur (eğer yeni ürünse)
                if not existing_product and product_data.get('stock', 0) > 0:
                    create_initial_stock_movement(product, product_data.get('stock', 0))
                
                success_count += 1
                
        except ValidationError as e:
            error_count += 1
            ImportError.objects.create(
                import_job=import_job,
                row_number=row_number,
                error_type='validation',
                error_message=str(e),
                row_data=row.to_dict()
            )
        except Exception as e:
            error_count += 1
            ImportError.objects.create(
                import_job=import_job,
                row_number=row_number,
                error_type='system',
                error_message=str(e),
                row_data=row.to_dict()
            )
            logger.error(f"Error processing row {row_number}: {str(e)}")
    
    return {
        'success': success_count,
        'errors': error_count,
        'updates': update_count
    }


def prepare_product_data(row: pd.Series) -> Dict[str, Any]:
    """
    DataFrame satırından ürün verilerini hazırlar ve doğrular.
    """
    from django.utils.text import slugify
    from django.utils import timezone
    
    # Gerekli alanları kontrol et
    required_fields = ['code', 'name', 'category', 'price', 'current_stock']
    for field in required_fields:
        if field not in row or pd.isna(row[field]):
            raise ValidationError(f"{field} alanı zorunludur")
    
    # Temel verileri hazırla
    product_data = {
        'name': str(row['name']).strip(),
        'slug': slugify(row['name']),
        'category': validate_category(row['category']),
        'family': validate_family(row.get('family')) if 'family' in row else None,
        'price': validate_price(row['price']),
        'cost': validate_price(row.get('cost')) if 'cost' in row and not pd.isna(row.get('cost')) else None,
        'tax_rate': float(row.get('tax_rate', 18)),
        'sale_price': validate_price(row.get('sale_price')) if 'sale_price' in row and not pd.isna(row.get('sale_price')) else None,
        'sale_end_date': validate_date(row.get('sale_end_date')) if 'sale_end_date' in row else None,
        'stock': int(row.get('current_stock', 0)),
        'threshold_stock': int(row.get('threshold_stock', 0)) if 'threshold_stock' in row else 0,
        'is_physical': validate_boolean(row.get('is_physical', True)) if 'is_physical' in row else True,
        'weight': float(row.get('weight', 0)) if 'weight' in row and not pd.isna(row.get('weight')) else 0,
        'dimensions': str(row.get('dimensions', '')) if 'dimensions' in row else '',
        'sku': str(row.get('sku', '')) if 'sku' in row else '',
        'barcode': str(row.get('barcode', '')) if 'barcode' in row else '',
        'status': validate_status(row.get('status')) if 'status' in row else 'available',
        'description': str(row.get('description', '')) if 'description' in row else ''
    }
    
    # Slug'ın benzersiz olmasını sağla
    base_slug = product_data['slug']
    if Product.objects.filter(slug=base_slug).exists():
        product_data['slug'] = f"{base_slug}-{int(timezone.now().timestamp())}"
    
    return product_data


def process_product_attributes(product: Product, row: pd.Series, 
                             import_job: ImportJob, row_number: int):
    """
    Ürün özelliklerini (renk, boyut, resim vb.) işler.
    """
    try:
        # Renk
        if 'color' in row and not pd.isna(row['color']):
            validate_attribute_value(product, 'Renk', row['color'])
        
        # Boyut
        if 'size' in row and not pd.isna(row['size']):
            validate_attribute_value(product, 'Boyut', row['size'])
        
        # Materyal
        if 'material' in row and not pd.isna(row['material']):
            validate_attribute_value(product, 'Materyal', row['material'])
        
        # Marka
        if 'brand' in row and not pd.isna(row['brand']):
            validate_attribute_value(product, 'Marka', row['brand'])
        
        # Resim URL'si
        if 'image_url' in row and not pd.isna(row['image_url']):
            process_image_url(product, row['image_url'])
            
    except Exception as e:
        logger.warning(f"Error processing attributes for product {product.code}: {str(e)}")
        ImportError.objects.create(
            import_job=import_job,
            row_number=row_number,
            error_type='other',
            error_message=f"Özellik işleme hatası: {str(e)}",
            column_name='attributes'
        )


def create_initial_stock_movement(product: Product, quantity: int):
    """
    Yeni ürün için başlangıç stok hareketi oluşturur.
    """
    try:
        StockMovement.objects.create(
            product=product,
            movement_type='adjustment',
            quantity=quantity,
            reference='İlk stok girişi',
            notes='Excel import ile oluşturuldu',
            created_by=None
        )
    except Exception as e:
        logger.error(f"Error creating stock movement for product {product.code}: {str(e)}")


@shared_task(bind=True, name='products.tasks.stock_adjustment')
def stock_adjustment_task(self, import_job_id: str, file_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stok düzeltmelerini Excel dosyasından asenkron olarak içe aktarır.
    
    Args:
        import_job_id: Import işlemi ID'si
        file_path: Excel dosyasının yolu
        settings: Import ayarları
    
    Returns:
        Import işlemi sonuç özeti
    """
    try:
        # Import job'ı al
        import_job = ImportJob.objects.get(id=import_job_id)
        import_job.status = 'processing'
        import_job.started_at = timezone.now()
        import_job.save()
        
        # Excel dosyasını oku
        df = pd.read_excel(file_path)
        total_rows = len(df)
        
        import_job.total_rows = total_rows
        import_job.save()
        
        # Chunk'lar halinde işle
        chunk_size = settings.get('chunk_size', CHUNK_SIZE)
        total_chunks = (total_rows + chunk_size - 1) // chunk_size
        import_job.total_chunks = total_chunks
        import_job.save()
        
        success_count = 0
        error_count = 0
        
        for chunk_num, start_idx in enumerate(range(0, total_rows, chunk_size)):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx]
            
            import_job.current_chunk = chunk_num + 1
            import_job.save()
            
            # Chunk'ı işle
            chunk_result = process_stock_adjustment_chunk(
                chunk=chunk,
                import_job=import_job,
                start_row=start_idx
            )
            
            success_count += chunk_result['success']
            error_count += chunk_result['errors']
            
            # İlerlemeyi güncelle
            import_job.processed_rows = end_idx
            import_job.success_count = success_count
            import_job.error_count = error_count
            import_job.update_progress()
            
            # Celery task durumunu güncelle
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': import_job.processed_rows,
                    'total': import_job.total_rows,
                    'progress': float(import_job.progress),
                    'success': success_count,
                    'errors': error_count
                }
            )
            
            # WebSocket ile ilerleme güncellemesi gönder
            send_import_progress(import_job_id, {
                'status': import_job.status,
                'progress': float(import_job.progress),
                'processed_rows': import_job.processed_rows,
                'total_rows': import_job.total_rows,
                'success_count': success_count,
                'error_count': error_count,
                'current_chunk': import_job.current_chunk,
                'total_chunks': import_job.total_chunks
            })
        
        # İşlemi tamamla
        import_job.result_summary = {
            'total_rows': total_rows,
            'success_count': success_count,
            'error_count': error_count
        }
        import_job.complete()
        
        # WebSocket ile tamamlanma bildirimi gönder
        send_import_completed(import_job_id, {
            'status': 'completed',
            'progress': 100,
            'processed_rows': import_job.processed_rows,
            'total_rows': import_job.total_rows,
            'success_count': success_count,
            'error_count': error_count,
            'result_summary': import_job.result_summary
        })
        
        return import_job.result_summary
        
    except Exception as e:
        logger.error(f"Stock adjustment task error: {str(e)}")
        
        if 'import_job' in locals():
            import_job.fail(str(e))
            
            # WebSocket ile hata bildirimi gönder
            send_import_failed(import_job_id, {
                'status': 'failed',
                'error_message': str(e),
                'processed_rows': import_job.processed_rows,
                'total_rows': import_job.total_rows,
                'success_count': import_job.success_count,
                'error_count': import_job.error_count
            })
        
        raise


def process_stock_adjustment_chunk(chunk: pd.DataFrame, import_job: ImportJob, 
                                 start_row: int) -> Dict[str, int]:
    """
    Stok düzeltmeleri chunk'ını işler.
    """
    success_count = 0
    error_count = 0
    
    # Sütun adlarını bul
    code_col = next((col for col in chunk.columns if 'product code' in col.lower()), None)
    qty_col = next((col for col in chunk.columns if 'quantity' in col.lower()), None)
    type_col = next((col for col in chunk.columns if 'movement type' in col.lower()), None)
    ref_col = next((col for col in chunk.columns if 'reference' in col.lower()), None)
    notes_col = next((col for col in chunk.columns if 'notes' in col.lower()), None)
    
    if not all([code_col, qty_col, type_col]):
        raise ValidationError("Gerekli sütunlar bulunamadı")
    
    for idx, row in chunk.iterrows():
        row_number = start_row + idx + 2
        
        try:
            with transaction.atomic():
                # Ürünü bul
                code = row[code_col]
                product = Product.objects.get(code=code)
                
                # Hareketi oluştur
                quantity = int(row[qty_col])
                movement_type = str(row[type_col]).lower()
                
                if movement_type not in ['in', 'out', 'adjustment']:
                    raise ValidationError(f"Geçersiz hareket tipi: {movement_type}")
                
                if movement_type == 'out':
                    quantity = -abs(quantity)
                elif movement_type == 'in':
                    quantity = abs(quantity)
                
                StockMovement.objects.create(
                    product=product,
                    movement_type=movement_type,
                    quantity=quantity,
                    reference=row.get(ref_col, 'Excel import') if ref_col else 'Excel import',
                    notes=row.get(notes_col, '') if notes_col else '',
                    created_by=None
                )
                
                # Stok güncelle
                if movement_type == 'adjustment':
                    product.stock = quantity
                else:
                    product.stock = max(0, product.stock + quantity)
                product.save(update_fields=['stock'])
                
                success_count += 1
                
        except Product.DoesNotExist:
            error_count += 1
            ImportError.objects.create(
                import_job=import_job,
                row_number=row_number,
                error_type='not_found',
                error_message=f'Ürün kodu {code} bulunamadı',
                row_data=row.to_dict()
            )
        except Exception as e:
            error_count += 1
            ImportError.objects.create(
                import_job=import_job,
                row_number=row_number,
                error_type='system',
                error_message=str(e),
                row_data=row.to_dict()
            )
    
    return {
        'success': success_count,
        'errors': error_count
    }


@shared_task(name='products.tasks.import_status')
def import_status_task(import_job_id: str) -> Dict[str, Any]:
    """
    Import işleminin durumunu kontrol eder.
    
    Args:
        import_job_id: Import işlemi ID'si
    
    Returns:
        İşlem durumu bilgileri
    """
    try:
        import_job = ImportJob.objects.get(id=import_job_id)
        
        # Hataları al
        errors = ImportError.objects.filter(import_job=import_job).values(
            'row_number', 'error_type', 'error_message', 'column_name'
        )[:100]  # İlk 100 hata
        
        return {
            'id': str(import_job.id),
            'status': import_job.status,
            'progress': float(import_job.progress),
            'total_rows': import_job.total_rows,
            'processed_rows': import_job.processed_rows,
            'success_count': import_job.success_count,
            'error_count': import_job.error_count,
            'errors': list(errors),
            'started_at': import_job.started_at.isoformat() if import_job.started_at else None,
            'completed_at': import_job.completed_at.isoformat() if import_job.completed_at else None,
            'result_summary': import_job.result_summary
        }
        
    except ImportJob.DoesNotExist:
        return {
            'error': 'Import işlemi bulunamadı'
        }