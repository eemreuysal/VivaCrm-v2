import os
import sys
import django
import pandas as pd

# Django ayarları
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order, OrderItem
from django.db.models import Count

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
        # Bu siparişin Excel'deki detayları
        excel_rows = df[df['SIPARIŞ NO'] == order_no]
        print(f'    Satır sayısı: {len(excel_rows)}')
        print(f'    Müşteri: {excel_rows.iloc[0]["MÜŞTERI ISMI"]}')
        print(f'    Tarih: {excel_rows.iloc[0]["SIPARIŞ TARIHI VE SAATI"]}')
        print()

# Sipariş öğesi sayısı kontrolü
order_item_count_db = OrderItem.objects.count()
print(f'\nVeritabanındaki sipariş öğesi sayısı: {order_item_count_db}')
print(f'Excel\'deki satır sayısı: {len(df)}')
print(f'Fark: {len(df) - order_item_count_db}')

# Her siparişin öğe sayısını kontrol et
print('\nSipariş öğe sayıları farklı olan siparişler:')
db_order_items = OrderItem.objects.values('order__order_number').annotate(count=Count('id'))
db_order_counts = {item['order__order_number']: item['count'] for item in db_order_items}

excel_order_counts = df['SIPARIŞ NO'].value_counts().to_dict()

# Ortak siparişlerde öğe sayısı farklılıkları
common_orders = excel_order_numbers & db_order_numbers
diff_count = 0
for order_no in common_orders:
    excel_count = excel_order_counts.get(order_no, 0)
    db_count = db_order_counts.get(order_no, 0)
    if excel_count != db_count:
        diff_count += 1
        if diff_count <= 10:  # İlk 10 farklılığı göster
            print(f'  {order_no}: Excel={excel_count}, DB={db_count}, Fark={excel_count - db_count}')

print(f'\nToplam farklı öğe sayısına sahip sipariş: {diff_count}')