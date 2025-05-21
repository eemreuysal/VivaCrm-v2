#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import ProductAttribute, ProductAttributeValue, Product
from django.utils.text import slugify

def add_attributes():
    test_product = Product.objects.filter(code='TEST-001').first()
    
    if test_product:
        # Renk
        attr_renk, _ = ProductAttribute.objects.get_or_create(
            name='Renk',
            defaults={'slug': 'renk'}
        )
        
        # Boyut
        attr_boyut, _ = ProductAttribute.objects.get_or_create(
            name='Boyut',
            defaults={'slug': 'boyut'}
        )
        
        # Materyal
        attr_materyal, _ = ProductAttribute.objects.get_or_create(
            name='Materyal',
            defaults={'slug': 'materyal'}
        )
        
        # Marka
        attr_marka, _ = ProductAttribute.objects.get_or_create(
            name='Marka',
            defaults={'slug': 'marka'}
        )
        
        # Değerler ekleme
        ProductAttributeValue.objects.update_or_create(
            product=test_product,
            attribute=attr_renk,
            defaults={'value': 'Kırmızı'}
        )
        
        ProductAttributeValue.objects.update_or_create(
            product=test_product,
            attribute=attr_boyut,
            defaults={'value': 'L'}
        )
        
        ProductAttributeValue.objects.update_or_create(
            product=test_product,
            attribute=attr_materyal,
            defaults={'value': 'Polyester'}
        )
        
        ProductAttributeValue.objects.update_or_create(
            product=test_product,
            attribute=attr_marka,
            defaults={'value': 'XYZ Marka'}
        )
        
        print('Ürüne renk, boyut, materyal ve marka özellikleri eklendi.')
    else:
        print('TEST-001 kodlu ürün bulunamadı!')

if __name__ == '__main__':
    add_attributes()