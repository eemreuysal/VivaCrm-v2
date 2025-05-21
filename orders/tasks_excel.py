"""
Sipariş Excel import için Celery task'ları
"""
from celery import shared_task
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal, ROUND_DOWN, InvalidOperation
import pandas as pd
import logging
import re
from typing import Dict, Any, List
from datetime import datetime

from core.models_import import ImportJob, ImportError, ImportHistory
from core.websocket_utils import send_import_progress, send_import_completed, send_import_failed
from .models import Order, OrderItem
from customers.models import Customer, Address
from products.models import Product

logger = logging.getLogger(__name__)

# Chunk size for processing
CHUNK_SIZE = 100


@shared_task(bind=True, name='orders.tasks.order_import')
def order_import_task(self, import_job_id: str, file_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Siparişleri Excel dosyasından asenkron olarak içe aktarır.
    
    Args:
        import_job_id: Import işlemi ID'si
        file_path: Excel dosyasının yolu
        settings: Import ayarları (update_existing, auto_create_products vb.)
    
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
            description=f'Sipariş import işlemi başlatıldı. Dosya: {file_path}'
        )
        
        # Excel dosyasını oku
        df = pd.read_excel(file_path)
        total_rows = len(df)
        
        import_job.total_rows = total_rows
        import_job.save()
        
        # Gerekli sütunları kontrol et
        required_columns = [
            "SIPARIŞ TARIHI VE SAATI", "SIPARIŞ NO", "MÜŞTERI ISMI", 
            "SKU", "ÜRÜN ISMI", "ADET", "BIRIM FIYAT"
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Gerekli sütunlar eksik: {', '.join(missing_columns)}")
        
        # Siparişleri grupla
        order_groups = df.groupby("SIPARIŞ NO")
        total_orders = len(order_groups)
        
        import_job.result_summary['total_orders'] = total_orders
        import_job.save()
        
        success_count = 0
        error_count = 0
        update_count = 0
        
        # Her sipariş grubunu işle
        for order_idx, (order_number, order_group) in enumerate(order_groups):
            try:
                # İlerlemeyi güncelle
                import_job.processed_rows = order_group.index[-1] + 1
                import_job.update_progress()
                
                # Celery task durumunu güncelle
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current_order': order_idx + 1,
                        'total_orders': total_orders,
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
                    'current_order': order_idx + 1,
                    'total_orders': total_orders
                })
                
                # Sipariş grubunu işle
                result = process_order_group(
                    order_number=order_number,
                    order_group=order_group,
                    import_job=import_job,
                    settings=settings
                )
                
                if result['success']:
                    success_count += result['items_count']
                    if result['updated']:
                        update_count += 1
                else:
                    error_count += result['items_count']
                    
            except Exception as e:
                error_count += len(order_group)
                first_row = order_group.iloc[0]
                row_number = first_row.name + 2
                
                ImportError.objects.create(
                    import_job=import_job,
                    row_number=row_number,
                    error_type='system',
                    error_message=f"Sipariş işleme hatası: {str(e)}",
                    row_data={'order_number': order_number}
                )
                logger.error(f"Error processing order {order_number}: {str(e)}")
        
        # İşlemi tamamla
        import_job.success_count = success_count
        import_job.error_count = error_count
        import_job.result_summary = {
            'total_rows': total_rows,
            'total_orders': total_orders,
            'success_count': success_count,
            'error_count': error_count,
            'update_count': update_count,
            'created_count': total_orders - update_count - (error_count // (total_rows // total_orders))
        }
        import_job.complete()
        
        # Geçmiş kaydı ekle
        ImportHistory.objects.create(
            import_job=import_job,
            action='İşlem tamamlandı',
            description=f'Başarıyla tamamlandı. {total_orders} sipariş işlendi, {error_count} hata oluştu.',
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
        logger.error(f"Order import task error: {str(e)}")
        
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


def process_order_group(order_number: str, order_group: pd.DataFrame, 
                       import_job: ImportJob, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bir sipariş grubunu (aynı sipariş numarasına sahip satırları) işler.
    
    Returns:
        İşlem sonucu
    """
    update_existing = settings.get('update_existing', False)
    auto_create_customers = settings.get('auto_create_customers', True)
    auto_create_products = settings.get('auto_create_products', True)
    
    first_row = order_group.iloc[0]
    row_number = first_row.name + 2
    
    try:
        with transaction.atomic():
            # Mevcut siparişi kontrol et
            existing_order = None
            if update_existing:
                try:
                    existing_order = Order.objects.get(order_number=order_number)
                except Order.DoesNotExist:
                    pass
            
            # Müşteriyi al veya oluştur
            customer = get_or_create_customer(
                first_row, 
                auto_create=auto_create_customers,
                import_job=import_job,
                row_number=row_number
            )
            
            if not customer:
                raise ValidationError("Müşteri bulunamadı veya oluşturulamadı")
            
            # Sipariş tarihini parse et
            order_date = parse_order_date(first_row["SIPARIŞ TARIHI VE SAATI"])
            
            # Sipariş notlarını hazırla
            order_notes = prepare_order_notes(first_row)
            
            # Siparişi oluştur veya güncelle
            if existing_order:
                order = existing_order
                order.customer = customer
                order.order_date = order_date
                order.notes = order_notes
                order.save()
                
                # Mevcut kalemleri temizle
                order.items.all().delete()
                
                updated = True
            else:
                order = Order.objects.create(
                    order_number=order_number,
                    customer=customer,
                    status='pending',
                    payment_status='pending',
                    order_date=order_date,
                    notes=order_notes,
                    owner=None
                )
                updated = False
            
            # Sipariş kalemlerini işle
            items_count = 0
            for idx, item_row in order_group.iterrows():
                item_row_number = idx + 2
                
                try:
                    process_order_item(
                        order=order,
                        item_row=item_row,
                        auto_create_products=auto_create_products,
                        import_job=import_job,
                        row_number=item_row_number
                    )
                    items_count += 1
                    
                except Exception as e:
                    ImportError.objects.create(
                        import_job=import_job,
                        row_number=item_row_number,
                        error_type='validation',
                        error_message=f"Sipariş kalemi hatası: {str(e)}",
                        row_data=item_row.to_dict()
                    )
                    raise
            
            # Sipariş toplamlarını hesapla
            order.calculate_totals()
            
            return {
                'success': True,
                'updated': updated,
                'items_count': items_count
            }
            
    except Exception as e:
        ImportError.objects.create(
            import_job=import_job,
            row_number=row_number,
            error_type='system',
            error_message=str(e),
            row_data=first_row.to_dict()
        )
        
        return {
            'success': False,
            'updated': False,
            'items_count': len(order_group)
        }


def get_or_create_customer(row: pd.Series, auto_create: bool, 
                          import_job: ImportJob, row_number: int) -> Customer:
    """
    Müşteriyi bulur veya gerekirse oluşturur.
    """
    customer_name = row["MÜŞTERI ISMI"]
    
    if pd.isna(customer_name) or not customer_name:
        raise ValidationError("Müşteri ismi zorunludur")
    
    # Mevcut müşteriyi ara
    customers = Customer.objects.filter(name__iexact=customer_name)
    if customers.exists():
        return customers.first()
    
    if not auto_create:
        raise ValidationError(f"Müşteri bulunamadı: {customer_name}")
    
    # Yeni müşteri oluştur
    # E-posta adresi oluştur
    email_name = re.sub(r'[^\w\s]', '', customer_name.lower())
    email_name = re.sub(r'\s+', '.', email_name.strip())
    
    if not email_name:
        email_name = "customer"
    
    customer = Customer.objects.create(
        name=customer_name,
        email=f"{email_name}@imported.com",
        phone="",
        company_name="",
        notes=f"Excel import'tan oluşturuldu. Eyalet: {row.get('EYALET', '')}, Şehir: {row.get('ŞEHIR', '')}"
    )
    
    # Adres oluştur (eğer bilgi varsa)
    if not pd.isna(row.get('ŞEHIR', '')) or not pd.isna(row.get('EYALET', '')):
        Address.objects.create(
            customer=customer,
            title="Import Adresi",
            type="shipping",
            city=row.get('ŞEHIR', '') if not pd.isna(row.get('ŞEHIR', '')) else "",
            state=row.get('EYALET', '') if not pd.isna(row.get('EYALET', '')) else "",
            address_line1="Excel import'tan oluşturuldu",
            country="Türkiye",
            is_default=True
        )
    
    ImportHistory.objects.create(
        import_job=import_job,
        action='Müşteri oluşturuldu',
        description=f'Yeni müşteri oluşturuldu: {customer_name}',
        metadata={'row_number': row_number}
    )
    
    return customer


def parse_order_date(date_str: str) -> datetime:
    """
    Sipariş tarihini parse eder.
    """
    try:
        # DD.MM.YYYY HH:MM formatını dene
        return pd.to_datetime(date_str, format="%d.%m.%Y %H:%M")
    except:
        try:
            # Pandas'ın otomatik parser'ını kullan
            return pd.to_datetime(date_str)
        except:
            # Varsayılan olarak şimdiki zamanı kullan
            logger.warning(f"Invalid date format: {date_str}, using current time")
            return timezone.now()


def prepare_order_notes(row: pd.Series) -> str:
    """
    Sipariş notlarını hazırlar.
    """
    notes_parts = ["Excel import'tan oluşturuldu"]
    
    if not pd.isna(row.get('EYALET', '')):
        notes_parts.append(f"Eyalet: {row['EYALET']}")
    
    if not pd.isna(row.get('ŞEHIR', '')):
        notes_parts.append(f"Şehir: {row['ŞEHIR']}")
    
    return ", ".join(notes_parts)


def process_order_item(order: Order, item_row: pd.Series, auto_create_products: bool,
                      import_job: ImportJob, row_number: int):
    """
    Sipariş kalemini işler.
    """
    # SKU ve ürün adını al
    sku = item_row["SKU"]
    product_name = item_row["ÜRÜN ISMI"]
    
    if pd.isna(sku) or pd.isna(product_name):
        raise ValidationError("SKU ve ürün ismi zorunludur")
    
    # Miktar ve fiyatı parse et
    try:
        quantity = int(item_row["ADET"])
    except:
        raise ValidationError(f"Geçersiz adet: {item_row['ADET']}")
    
    # Fiyatı parse et (virgüllü format)
    unit_price_str = str(item_row["BIRIM FIYAT"]).replace(',', '.')
    try:
        unit_price = Decimal(unit_price_str)
    except InvalidOperation:
        raise ValidationError(f"Geçersiz birim fiyat: {item_row['BIRIM FIYAT']}")
    
    # İndirimi parse et
    discount_amount = Decimal('0')
    if "BIRIM INDIRIM" in item_row and not pd.isna(item_row["BIRIM INDIRIM"]):
        discount_str = str(item_row["BIRIM INDIRIM"]).replace(',', '.')
        try:
            discount_amount = Decimal(discount_str)
        except InvalidOperation:
            logger.warning(f"Invalid discount amount: {item_row['BIRIM INDIRIM']}")
    
    # Ürünü bul veya oluştur
    product = get_or_create_product(
        sku=sku,
        product_name=product_name,
        unit_price=unit_price,
        barcode=item_row.get("GTIN", ""),
        auto_create=auto_create_products,
        import_job=import_job,
        row_number=row_number
    )
    
    if not product:
        raise ValidationError(f"Ürün bulunamadı: {sku}")
    
    # Ondalık basamakları düzelt
    unit_price = unit_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    discount_amount = discount_amount.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    # Sipariş kalemini oluştur
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        discount_amount=discount_amount,
        tax_rate=product.tax_rate
    )


def get_or_create_product(sku: str, product_name: str, unit_price: Decimal,
                         barcode: str, auto_create: bool, import_job: ImportJob,
                         row_number: int) -> Product:
    """
    Ürünü bulur veya gerekirse oluşturur.
    """
    # SKU ile ara
    products = Product.objects.filter(sku=sku)
    if products.exists():
        return products.first()
    
    # Kod ile ara
    products = Product.objects.filter(code=sku)
    if products.exists():
        return products.first()
    
    if not auto_create:
        return None
    
    # Yeni ürün oluştur
    product = Product.objects.create(
        name=product_name,
        code=sku,
        sku=sku,
        barcode=barcode if not pd.isna(barcode) else "",
        description="Sipariş import'tan otomatik oluşturuldu",
        price=unit_price,
        tax_rate=18,  # Varsayılan KDV oranı
        stock=0,  # Başlangıç stoğu 0
        is_active=True
    )
    
    ImportHistory.objects.create(
        import_job=import_job,
        action='Ürün oluşturuldu',
        description=f'Yeni ürün oluşturuldu: {product_name} (SKU: {sku})',
        metadata={'row_number': row_number}
    )
    
    return product


@shared_task(name='orders.tasks.import_status')
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
        
        # Geçmişi al
        history = ImportHistory.objects.filter(import_job=import_job).values(
            'action', 'description', 'created_at'
        ).order_by('-created_at')[:20]  # Son 20 kayıt
        
        return {
            'id': str(import_job.id),
            'status': import_job.status,
            'progress': float(import_job.progress),
            'total_rows': import_job.total_rows,
            'processed_rows': import_job.processed_rows,
            'success_count': import_job.success_count,
            'error_count': import_job.error_count,
            'current_chunk': import_job.current_chunk,
            'total_chunks': import_job.total_chunks,
            'errors': list(errors),
            'history': list(history),
            'started_at': import_job.started_at.isoformat() if import_job.started_at else None,
            'completed_at': import_job.completed_at.isoformat() if import_job.completed_at else None,
            'result_summary': import_job.result_summary
        }
        
    except ImportJob.DoesNotExist:
        return {
            'error': 'Import işlemi bulunamadı'
        }