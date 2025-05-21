"""
Tablo bileşenleri için özel template filtreleri.

Bu modül, responsive_table.html gibi tablo bileşenlerinin
veri işleme ihtiyaçlarını karşılamak için özel filtreler sağlar.
"""

from django import template
from django.template.defaultfilters import stringfilter
import json
from datetime import datetime

register = template.Library()


@register.filter
def get_dict_value(dictionary, key):
    """
    Dictionary, object veya nested obje/dict'ten değer alır.
    
    Örnek kullanım:
    {{ product|get_dict_value:'category.name' }} - Ürünün kategorisinin adını getirir
    {{ order|get_dict_value:'customer.email' }} - Siparişin müşterisinin emailini getirir
    
    Args:
        dictionary: Değerin alınacağı sözlük veya obje
        key: Alınacak değerin anahtarı, nokta (.) ile nested erişim için
    
    Returns:
        İstenen değer veya değer bulunamadıysa boş string
    """
    if not dictionary or not key:
        return ''
    
    # Nested keys (örn: "category.name")
    if '.' in key:
        parts = key.split('.', 1)
        first_key, rest_keys = parts[0], parts[1]
        
        if isinstance(dictionary, dict):
            nested_value = dictionary.get(first_key, '')
        else:
            nested_value = getattr(dictionary, first_key, '')
            
        if nested_value:
            return get_dict_value(nested_value, rest_keys)
        return ''
    
    # Dictionary ise key ile eriş
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    
    # Object ise attribute olarak eriş
    try:
        # İlişkili modeller için _id ile biten alanlar da kontrol edilir
        value = getattr(dictionary, key, None)
        if value is None and not key.endswith('_id'):
            value = getattr(dictionary, f"{key}_id", '')
        return value
    except (AttributeError, TypeError):
        return ''


@register.filter
def apply_format(value, format_type):
    """
    Değeri belirtilen formata göre biçimlendirir.
    
    Desteklenen format tipleri:
    - currency: Para birimi formatı (ör: 150,75 ₺)
    - date: Tarih formatı (ör: 15 Ocak 2023)
    - datetime: Tarih ve saat formatı (ör: 15 Ocak 2023 14:30)
    - boolean: Evet/Hayır
    - percent: Yüzde formatı (ör: %85)
    
    Args:
        value: Biçimlendirilecek değer
        format_type: Biçimlendirme tipi
    
    Returns:
        Biçimlendirilmiş değer veya orijinal değer
    """
    if value is None:
        return ''
    
    # Para birimi (₺)
    if format_type == 'currency':
        try:
            # String ise float'a çevir
            if isinstance(value, str):
                value = float(value.replace(',', '.'))
            return f"{float(value):.2f} ₺"
        except (ValueError, TypeError):
            return value
    
    # Tarih (gün ay yıl)
    if format_type == 'date':
        if isinstance(value, datetime):
            try:
                return value.strftime('%d %B %Y')
            except:
                return value
        elif isinstance(value, str):
            try:
                date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return date_obj.strftime('%d %B %Y')
            except:
                return value
        return value
    
    # Tarih ve saat
    if format_type == 'datetime':
        if isinstance(value, datetime):
            try:
                return value.strftime('%d %B %Y %H:%M')
            except:
                return value
        elif isinstance(value, str):
            try:
                date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return date_obj.strftime('%d %B %Y %H:%M')
            except:
                return value
        return value
    
    # Boolean (Evet/Hayır)
    if format_type == 'boolean':
        if value in (True, 'True', 'true', 1, '1', 'yes', 'Yes'):
            return "Evet"
        else:
            return "Hayır"
    
    # Yüzde
    if format_type == 'percent':
        try:
            # String ise float'a çevir
            if isinstance(value, str):
                value = float(value.replace(',', '.'))
            return f"%{float(value):.1f}"
        except (ValueError, TypeError):
            return value
    
    # Desteklenmeyen format
    return value