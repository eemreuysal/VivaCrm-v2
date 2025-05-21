from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from orders.models import Order


class Command(BaseCommand):
    help = "Mevcut siparişlerin segment bilgilerini günceller (FBA/FBM)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Segment güncelleme işlemi başlıyor..."))
        
        # segment boş olan siparişleri bul
        orders_without_segment = Order.objects.filter(segment__isnull=True)
        count = orders_without_segment.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING("Güncellenecek sipariş bulunamadı."))
            return
        
        updated_count = 0
        fba_count = 0
        fbm_count = 0
        
        for order in orders_without_segment:
            if order.customer:
                # Müşteri ismi "*** ***" ise FBA, değilse FBM
                if order.customer.name and order.customer.name.strip() == "*** ***":
                    order.segment = "FBA"
                    fba_count += 1
                else:
                    order.segment = "FBM"
                    fbm_count += 1
                
                order.save()
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"{updated_count} sipariş güncellendi.\n"
                f"FBA: {fba_count}\n"
                f"FBM: {fbm_count}"
            )
        )
