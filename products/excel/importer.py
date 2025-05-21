"""
Ürün Excel import işlemleri.
Core base class'ları extend eder.
"""
from typing import Dict, Any, Optional
from decimal import Decimal
import logging
from django.db import transaction
from django.utils.text import slugify

from core.excel.base import BaseExcelImporter
from core.excel.validators import ExcelValidators
from core.excel.exceptions import (
    ValidationError,
    CategoryNotFoundError,
    ProductFamilyNotFoundError,
    InvalidPriceError
)
from products.models import Product, Category, ProductFamily, ProductImage
from urllib.parse import urlparse
import requests
from io import BytesIO
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class ProductExcelImporter(BaseExcelImporter):
    """
    Ürün-spesifik Excel importer.
    Kategori ve aile oluşturma, resim indirme gibi gelişmiş özellikler içerir.
    """
    
    def __init__(self):
        super().__init__(Product)
        self.validators = ExcelValidators()
        self._category_cache = {}
        self._family_cache = {}
        self._sku_cache = set()  # Duplicate kontrolü için
        
    def get_field_mapping(self) -> Dict[str, str]:
        """Excel başlıklarını model field'larına map'le"""
        return {
            'Ürün Kodu': 'code',
            'Ürün Adı': 'name',
            'Kategori': 'category',
            'Ürün Ailesi': 'family',
            'Fiyat': 'price',
            'İndirimli Fiyat': 'sale_price',
            'İndirim Bitiş Tarihi': 'sale_end_date',
            'Maliyet': 'cost',
            'KDV Oranı (%)': 'tax_rate',
            'Stok': 'current_stock',
            'Minimum Stok': 'threshold_stock',
            'SKU': 'sku',
            'Barkod': 'barcode',
            'Ağırlık (kg)': 'weight',
            'Boyutlar': 'dimensions',
            'Malzeme': 'material',
            'Marka': 'brand',
            'Resim URL': 'image_url',
            'Fiziksel Ürün': 'is_physical',
            'Durum': 'status',
            'Açıklama': 'description'
        }
    
    def validate_row(self, row_data: Dict[str, Any], row_index: int) -> bool:
        """Ürün verilerini doğrula"""
        try:
            # Zorunlu alanlar
            self.validators.validate_required(row_data.get('code'), 'Ürün Kodu')
            self.validators.validate_required(row_data.get('name'), 'Ürün Adı')
            self.validators.validate_required(row_data.get('price'), 'Fiyat')
            
            # Fiyat doğrulamaları
            price = self.validators.validate_decimal(
                row_data.get('price'),
                'Fiyat',
                min_value=Decimal('0')
            )
            
            # İndirimli fiyat kontrolü
            if row_data.get('sale_price'):
                sale_price = self.validators.validate_decimal(
                    row_data['sale_price'],
                    'İndirimli Fiyat',
                    min_value=Decimal('0')
                )
                
                # İndirimli fiyat normal fiyattan yüksek olamaz
                if sale_price and price and sale_price > price:
                    raise InvalidPriceError(
                        "İndirimli fiyat normal fiyattan yüksek olamaz",
                        row=row_index,
                        field='sale_price'
                    )
            
            # Maliyet kontrolü
            if row_data.get('cost'):
                self.validators.validate_decimal(
                    row_data['cost'],
                    'Maliyet',
                    min_value=Decimal('0')
                )
            
            # KDV oranı kontrolü
            if row_data.get('tax_rate'):
                self.validators.validate_decimal(
                    row_data['tax_rate'],
                    'KDV Oranı',
                    min_value=Decimal('0'),
                    max_value=Decimal('100')
                )
            
            # Stok kontrolü
            if row_data.get('current_stock'):
                self.validators.validate_integer(
                    row_data['current_stock'],
                    'Stok',
                    min_value=0
                )
            
            # Kategori kontrolü
            if row_data.get('category'):
                self._validate_category_name(row_data['category'])
            
            # Status kontrolü
            if row_data.get('status'):
                self.validators.validate_choice(
                    row_data['status'],
                    'Durum',
                    ['available', 'unavailable', 'coming_soon', 'discontinued']
                )
            
            # Boolean kontrolü
            if row_data.get('is_physical') is not None:
                self.validators.validate_boolean(
                    row_data['is_physical'],
                    'Fiziksel Ürün'
                )
            
            # URL kontrolü
            if row_data.get('image_url'):
                self.validators.validate_url(row_data['image_url'], 'Resim URL')
            
            # SKU duplicate kontrolü
            sku = row_data.get('sku') or row_data.get('code')
            if sku in self._sku_cache:
                raise ValidationError(f"Duplicate SKU: {sku}", row=row_index)
            
            return True
            
        except ValidationError as e:
            # Field bilgisi ekle
            if not hasattr(e, 'row'):
                e.row = row_index
            raise
        except Exception as e:
            logger.error(f"Satır {row_index} validasyon hatası: {str(e)}")
            raise ValidationError(str(e), row=row_index)
    
    def process_row(self, row_data: Dict[str, Any], row_index: int) -> Optional[Product]:
        """Tek bir satırı işle ve ürün oluştur/güncelle"""
        try:
            # Kategori ve aile işlemleri
            category = self._get_or_create_category(row_data.get('category'))
            family = self._get_or_create_family(row_data.get('family'))
            
            # Ürün verilerini hazırla
            product_data = self._prepare_product_data(row_data, category, family)
            
            # Transaction içinde ürün oluştur/güncelle
            with transaction.atomic():
                product, created = Product.objects.update_or_create(
                    code=product_data['code'],
                    defaults=product_data
                )
                
                # SKU'yu cache'e ekle
                self._sku_cache.add(product.sku)
                
                # Resim işleme
                if row_data.get('image_url'):
                    self._handle_product_image(product, row_data['image_url'], row_index)
                
                # Log
                action = "oluşturuldu" if created else "güncellendi"
                logger.info(f"Ürün {action}: {product.code} - {product.name}")
                
                return product
                
        except Exception as e:
            logger.error(f"Satır {row_index} işleme hatası: {str(e)}")
            raise
    
    def _prepare_product_data(self, row_data: Dict[str, Any], category: Optional[Category], 
                             family: Optional[ProductFamily]) -> Dict[str, Any]:
        """Ürün verilerini model için hazırla"""
        data = {
            'code': row_data['code'].strip(),
            'name': row_data['name'].strip(),
            'category': category,
            'family': family,
            'price': self.validators.validate_decimal(row_data.get('price'), 'Fiyat'),
            'cost': self.validators.validate_decimal(row_data.get('cost'), 'Maliyet', allow_none=True),
            'tax_rate': self.validators.validate_decimal(
                row_data.get('tax_rate'), 
                'KDV Oranı', 
                allow_none=True
            ) or Decimal('18'),  # Varsayılan %18
            'current_stock': self.validators.validate_integer(
                row_data.get('current_stock'), 
                'Stok', 
                allow_none=True
            ) or 0,
            'threshold_stock': self.validators.validate_integer(
                row_data.get('threshold_stock'), 
                'Minimum Stok', 
                allow_none=True
            ) or 0,
            'sku': row_data.get('sku', '').strip() or row_data['code'].strip(),
            'barcode': row_data.get('barcode', '').strip() or None,
            'is_physical': self.validators.validate_boolean(
                row_data.get('is_physical'), 
                'Fiziksel Ürün', 
                allow_none=True
            ) or True,
            'description': row_data.get('description', '').strip()
        }
        
        # Opsiyonel alanlar
        if row_data.get('sale_price'):
            data['sale_price'] = self.validators.validate_decimal(
                row_data['sale_price'], 
                'İndirimli Fiyat', 
                allow_none=True
            )
        
        if row_data.get('sale_end_date'):
            data['sale_end_date'] = self.validators.validate_date(
                row_data['sale_end_date'], 
                'İndirim Bitiş Tarihi', 
                allow_none=True
            )
        
        if row_data.get('weight'):
            data['weight'] = self.validators.validate_decimal(
                row_data['weight'], 
                'Ağırlık', 
                allow_none=True,
                min_value=Decimal('0')
            )
        
        if row_data.get('dimensions'):
            data['dimensions'] = row_data['dimensions'].strip()
        
        if row_data.get('status'):
            data['status'] = self.validators.validate_choice(
                row_data['status'],
                'Durum',
                Product.STATUS_CHOICES
            )
        else:
            data['status'] = 'available'  # Varsayılan
        
        # Özel alanlar (attributes içinde saklanacak)
        if row_data.get('material'):
            data['material'] = row_data['material'].strip()
        
        if row_data.get('brand'):
            data['brand'] = row_data['brand'].strip()
        
        return data
    
    def _get_or_create_category(self, category_name: str) -> Optional[Category]:
        """Kategori al veya oluştur (cache ile)"""
        if not category_name:
            return None
        
        category_name = category_name.strip()
        
        # Cache kontrol
        if category_name in self._category_cache:
            return self._category_cache[category_name]
        
        # Veritabanında ara (case-insensitive)
        try:
            category = Category.objects.get(name__iexact=category_name)
        except Category.DoesNotExist:
            # Yeni kategori oluştur
            category = Category.objects.create(
                name=category_name,
                slug=slugify(category_name)
            )
            self.warnings.append({
                'message': f"Yeni kategori oluşturuldu: {category_name}"
            })
            logger.info(f"Yeni kategori oluşturuldu: {category_name}")
        
        # Cache'e ekle
        self._category_cache[category_name] = category
        return category
    
    def _get_or_create_family(self, family_name: str) -> Optional[ProductFamily]:
        """Ürün ailesi al veya oluştur (cache ile)"""
        if not family_name:
            return None
        
        family_name = family_name.strip()
        
        # Cache kontrol
        if family_name in self._family_cache:
            return self._family_cache[family_name]
        
        # Veritabanında ara (case-insensitive)
        try:
            family = ProductFamily.objects.get(name__iexact=family_name)
        except ProductFamily.DoesNotExist:
            # Yeni aile oluştur
            family = ProductFamily.objects.create(
                name=family_name,
                slug=slugify(family_name)
            )
            self.warnings.append({
                'message': f"Yeni ürün ailesi oluşturuldu: {family_name}"
            })
            logger.info(f"Yeni ürün ailesi oluşturuldu: {family_name}")
        
        # Cache'e ekle
        self._family_cache[family_name] = family
        return family
    
    def _validate_category_name(self, category_name: str):
        """Kategori adını doğrula"""
        if not category_name:
            return
        
        # Özel karakterler veya SQL injection kontrolü
        forbidden_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
        for char in forbidden_chars:
            if char in category_name:
                raise ValidationError(
                    f"Kategori adı geçersiz karakterler içeriyor: {char}"
                )
    
    def _handle_product_image(self, product: Product, image_url: str, row_index: int):
        """Ürün resmini URL'den indir ve kaydet"""
        try:
            # Mevcut resim varsa kontrol et
            if product.images.filter(is_primary=True).exists():
                logger.info(f"Ürün {product.code} için resim zaten mevcut")
                return
            
            # URL'den resmi indir
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Dosya adını oluştur
            url_path = urlparse(image_url).path
            file_name = url_path.split('/')[-1] or f"{product.code}.jpg"
            
            # İçeriği al
            file_content = ContentFile(response.content)
            
            # ProductImage oluştur
            product_image = ProductImage(
                product=product,
                is_primary=True
            )
            product_image.image.save(file_name, file_content, save=True)
            
            logger.info(f"Ürün resmi indirildi: {product.code}")
            
        except requests.exceptions.RequestException as e:
            self.warnings.append({
                'row': row_index,
                'message': f"Resim indirilemedi: {str(e)}",
                'url': image_url
            })
            logger.warning(f"Resim indirilemedi {image_url}: {str(e)}")
        except Exception as e:
            self.warnings.append({
                'row': row_index,
                'message': f"Resim işleme hatası: {str(e)}",
                'url': image_url
            })
            logger.error(f"Resim işleme hatası {image_url}: {str(e)}")