import os
import sys
import django
import pandas as pd

# Django ayarları
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order, OrderItem
from products.models import Product
from customers.models import Customer
from core.models_import import ImportTask, ImportSummary, DetailedImportResult

# Excel dosyasını oku
df = pd.read_excel('/Users/emreuysal/Downloads/siparis_excel_sablonu.xlsx')

# Excel'deki sipariş numaraları
excel_order_numbers = set(df['SIPARIŞ NO'].unique())
print(f'Excel\'deki benzersiz sipariş sayısı: {len(excel_order_numbers)}')

# Veritabanındaki sipariş numaraları
db_order_numbers = set(Order.objects.values_list('order_number', flat=True))
print(f'Veritabanındaki benzersiz sipariş sayısı: {len(db_order_numbers)}')

# Eksik siparişler
missing_orders = excel_order_numbers - db_order_numbers
print(f'\nVeritabanında olmayan sipariş sayısı: {len(missing_orders)}')
if missing_orders:
    print('Eksik siparişler:')
    for order_no in missing_orders:
        print(f'  - {order_no}')
        excel_rows = df[df['SIPARIŞ NO'] == order_no]
        print(f'    Satır sayısı: {len(excel_rows)}')
        print(f'    Müşteri: {excel_rows.iloc[0]["MÜŞTERI ISMI"]}')
        print()

# Fazla siparişler (veritabanında olup Excel'de olmayan)
extra_orders = db_order_numbers - excel_order_numbers
print(f'\nExcel\'de olmayan sipariş sayısı: {len(extra_orders)}')
if extra_orders:
    print('İlk 10 fazla sipariş:')
    for i, order_no in enumerate(list(extra_orders)):
        if i >= 10:
            break
        print(f'  - {order_no}')

# Sipariş öğesi sayısı kontrolü
order_item_count_db = OrderItem.objects.count()
print(f'\nVeritabanındaki sipariş öğesi sayısı: {order_item_count_db}')
print(f'Excel\'deki satır sayısı: {len(df)}')
print(f'Fark: {len(df) - order_item_count_db}')

# Her siparişin öğe sayısını kontrol et
from django.db.models import Count
db_order_items = OrderItem.objects.values('order__order_number').annotate(count=Count('id'))
db_order_counts = {item['order__order_number']: item['count'] for item in db_order_items}

excel_order_counts = df['SIPARIŞ NO'].value_counts().to_dict()

# Ortak siparişlerde öğe sayısı farklılıkları
common_orders = excel_order_numbers & db_order_numbers
diff_count = 0
diff_items = []
for order_no in common_orders:
    excel_count = excel_order_counts.get(order_no, 0)
    db_count = db_order_counts.get(order_no, 0)
    if excel_count != db_count:
        diff_count += 1
        diff_items.append((order_no, excel_count, db_count))

print(f'\nToplam farklı öğe sayısına sahip sipariş: {diff_count}')
if diff_items:
    print('İlk 10 farklılık:')
    for i, (order_no, excel_count, db_count) in enumerate(diff_items[:10]):
        print(f'  {order_no}: Excel={excel_count}, DB={db_count}, Fark={excel_count - db_count}')

# Müşteri kontrolü
excel_customers = set(df['MÜŞTERI ISMI'].unique())
print(f'\n\nMÜŞTERİ ANALİZİ:')
print(f'Excel\'deki benzersiz müşteri sayısı: {len(excel_customers)}')
print(f'Veritabanındaki müşteri sayısı: {Customer.objects.count()}')

# Excel'deki müşterilerden veritabanında olmayanlar
missing_customers = []
for customer_name in excel_customers:
    if not Customer.objects.filter(name__iexact=customer_name).exists():
        missing_customers.append(customer_name)

print(f'Veritabanında olmayan müşteri sayısı: {len(missing_customers)}')
if missing_customers:
    print('İlk 10 eksik müşteri:')
    for i, name in enumerate(missing_customers[:10]):
        print(f'  - {name}')

# SKU analizi
excel_skus = set(df['SKU'].unique())
db_skus = set(Product.objects.values_list('sku', flat=True))
missing_skus = excel_skus - db_skus

print(f'\n\nÜRÜN ANALİZİ:')
print(f'Excel\'deki benzersiz SKU sayısı: {len(excel_skus)}')
print(f'Veritabanındaki ürün sayısı: {Product.objects.count()}')
print(f'Veritabanında olmayan SKU sayısı: {len(missing_skus)}')
if missing_skus:
    print('İlk 10 eksik SKU:')
    for i, sku in enumerate(list(missing_skus)[:10]):
        print(f'  - {sku}')
        excel_product = df[df['SKU'] == sku].iloc[0]
        print(f'    Ürün: {excel_product["ÜRÜN ISMI"]}')

# ImportTask analizi
print('\n\nIMPORT TASK ANALİZİ:')
import_tasks = ImportTask.objects.filter(type='order').order_by('-created_at')[:5]
if import_tasks.exists():
    for task in import_tasks:
        print(f'\nImport Task #{task.id}:')
        print(f'  Tarih: {task.created_at}')
        print(f'  Durum: {task.status}')
        print(f'  Dosya: {task.file_name}')
        if hasattr(task, 'summary'):
            summary = task.summary
            print(f'  Toplam: {summary.total_rows}')
            print(f'  Başarılı: {summary.successful_rows}')
            print(f'  Başarısız: {summary.failed_rows}')
            print(f'  Güncellenen: {summary.updated_rows}')
else:
    print('Henüz import task kaydı yok.')

# En son import detayları
latest_import = import_tasks.first() if import_tasks.exists() else None
if latest_import:
    print(f'\n\nEN SON IMPORT DETAYLARI (Task #{latest_import.id}):')
    failed_results = DetailedImportResult.objects.filter(
        import_task=latest_import,
        status='failed'
    )[:10]
    
    if failed_results.exists():
        print(f'İlk 10 hata:')
        for result in failed_results:
            print(f'  Satır {result.row_number}: {result.error_message}')
            if result.data:
                print(f'    Sipariş No: {result.data.get("SIPARIŞ NO", "N/A")}')
                print(f'    Müşteri: {result.data.get("MÜŞTERI ISMI", "N/A")}')
    else:
        print('Bu import\'ta hata yok.')