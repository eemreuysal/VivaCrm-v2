#!/usr/bin/env python
import os
import django

# Django ayarlarını yükle
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from customers.models import Customer, Address, Contact

# Müşteri verilerini temizleme
print(f"Silme öncesi müşteri sayısı: {Customer.objects.count()}")
print(f"Silme öncesi adres sayısı: {Address.objects.count()}")
print(f"Silme öncesi iletişim sayısı: {Contact.objects.count()}")

# Tüm müşterileri siliyoruz
Customer.objects.all().delete()

print(f"Silme sonrası müşteri sayısı: {Customer.objects.count()}")
print(f"Silme sonrası adres sayısı: {Address.objects.count()}")
print(f"Silme sonrası iletişim sayısı: {Contact.objects.count()}")

print("Müşteri verileri başarıyla temizlendi.")