# Generated manually
from django.db import migrations


def update_existing_segments(apps, schema_editor):
    """
    Mevcut siparişler için segment bilgisini güncelle
    Müşteri ismi "*** ***" ise FBA, değilse FBM
    """
    Order = apps.get_model('orders', 'Order')
    
    # Tüm siparişleri güncelle
    for order in Order.objects.filter(segment__isnull=True):
        if order.customer and order.customer.name:
            if order.customer.name.strip() == "*** ***":
                order.segment = 'FBA'
            else:
                order.segment = 'FBM'
            order.save()


def reverse_update_segments(apps, schema_editor):
    """
    Geriye dönük işlem için segment bilgisini temizle
    """
    Order = apps.get_model('orders', 'Order')
    Order.objects.all().update(segment=None)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_add_segment_field'),
    ]

    operations = [
        migrations.RunPython(update_existing_segments, reverse_update_segments),
    ]