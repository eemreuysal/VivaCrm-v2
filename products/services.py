"""
Products modülü için servis katmanı.
Business logic kod tekrarını önlemek için merkezi bir yer sağlar.
"""
from decimal import Decimal
from django.utils.text import slugify
from django.core.cache import cache
from django.utils import timezone
import logging

from .models import Product, Category, ProductFamily, StockMovement

logger = logging.getLogger(__name__)


class SlugService:
    """
    Slug oluşturma ve doğrulama işlemleri için servis.
    """
    
    @staticmethod
    def generate_slug(name, model_class, instance=None):
        """
        Verilen isim için benzersiz slug oluştur.
        
        Args:
            name: Slugify edilecek isim
            model_class: Slug'ın benzersiz olması gereken model
            instance: Güncelleme durumunda mevcut instance
            
        Returns:
            Benzersiz slug string
        """
        base_slug = slugify(name)
        slug = base_slug
        
        # Mevcut instance ise ve slug değişmediyse
        if instance and instance.slug == slug:
            return slug
            
        # Benzersiz slug kontrolü
        counter = 1
        while model_class.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug


class StockService:
    """
    Stok işlemleri için servis.
    """
    
    @staticmethod
    def calculate_new_stock(product, quantity, movement_type):
        """
        Hareket tipine göre yeni stok seviyesini hesapla.
        
        Args:
            product: Product instance
            quantity: Hareket miktarı
            movement_type: Hareket tipi
            
        Returns:
            previous_stock, new_stock tuple
        """
        previous_stock = product.stock
        
        if movement_type in ['purchase', 'return', 'adjustment', 'inventory']:
            new_stock = previous_stock + quantity
        else:  # sale, waste, transfer
            new_stock = max(0, previous_stock - abs(quantity))
            
        return previous_stock, new_stock
    
    @staticmethod
    def calculate_average_cost(product, quantity, unit_cost):
        """
        Ağırlıklı ortalama maliyet hesapla.
        
        Args:
            product: Product instance
            quantity: Yeni ürün miktarı
            unit_cost: Birim maliyet
            
        Returns:
            Yeni ortalama maliyet
        """
        try:
            if product.stock > 0 and product.cost:
                total_old_value = product.stock * product.cost
                total_new_value = quantity * unit_cost
                new_stock = product.stock + quantity
                return (total_old_value + total_new_value) / new_stock
            else:
                return unit_cost
        except Exception as e:
            logger.error(f"Average cost calculation error: {str(e)}")
            return unit_cost
    
    @staticmethod
    def prepare_stock_movement(stock_movement):
        """
        StockMovement kaydını kaydetmeden önce hazırla.
        
        Args:
            stock_movement: StockMovement instance
            
        Returns:
            Hazırlanmış StockMovement
        """
        try:
            # Önceki ve yeni stok hesapla
            previous_stock, new_stock = StockService.calculate_new_stock(
                stock_movement.product,
                stock_movement.quantity,
                stock_movement.movement_type
            )
            
            stock_movement.previous_stock = previous_stock
            stock_movement.new_stock = new_stock
            
            # Maliyet güncelleme
            if stock_movement.unit_cost and stock_movement.movement_type == 'purchase':
                new_cost = StockService.calculate_average_cost(
                    stock_movement.product,
                    stock_movement.quantity,
                    stock_movement.unit_cost
                )
                stock_movement.product.cost = new_cost
                
        except Exception as e:
            logger.error(f"Error in prepare_stock_movement: {str(e)}")
            if not hasattr(stock_movement, 'previous_stock'):
                stock_movement.previous_stock = 0
            if not hasattr(stock_movement, 'new_stock'):
                stock_movement.new_stock = 0
                
        return stock_movement
    
    @staticmethod
    def update_product_stock(product_id, new_stock, cost=None):
        """
        Ürün stok ve maliyet bilgisini güncelle.
        
        Args:
            product_id: Ürün ID
            new_stock: Yeni stok miktarı
            cost: Yeni maliyet (opsiyonel)
            
        Returns:
            Güncellenmiş ürün
        """
        try:
            update_fields = ['stock', 'updated_at']
            product = Product.objects.get(id=product_id)
            product.stock = new_stock
            
            if cost is not None:
                product.cost = cost
                update_fields.append('cost')
                
            product.save(update_fields=update_fields)
            
            # Cache temizle
            cache.delete(f'product_{product_id}')
            cache.delete('products_low_stock')
            
            return product
            
        except Product.DoesNotExist:
            logger.error(f"Product not found for ID: {product_id}")
        except Exception as e:
            logger.error(f"Error updating product stock: {str(e)}")


class ProductService:
    """
    Ürün işlemleri için servis.
    """
    
    @staticmethod
    def get_or_create_category(category_name):
        """
        Kategori adına göre kategori al veya oluştur.
        
        Args:
            category_name: Kategori adı
            
        Returns:
            Category instance
        """
        if not category_name:
            return None
            
        category_name = category_name.strip()
        
        # Önce case insensitive ara
        categories = Category.objects.filter(name__iexact=category_name)
        if categories.exists():
            return categories.first()
        
        # Boşlukları normalize et
        normalized_name = ' '.join(category_name.split())
        categories = Category.objects.filter(name__iexact=normalized_name)
        if categories.exists():
            return categories.first()
        
        # Yeni kategori oluştur
        slug = SlugService.generate_slug(category_name, Category)
        category = Category.objects.create(
            name=category_name,
            slug=slug
        )
        
        logger.info(f"New category created: {category_name}")
        return category
    
    @staticmethod
    def get_or_create_family(family_name):
        """
        Aile adına göre ürün ailesi al veya oluştur.
        
        Args:
            family_name: Aile adı
            
        Returns:
            ProductFamily instance
        """
        if not family_name:
            return None
            
        family_name = family_name.strip()
        
        # Önce case insensitive ara
        families = ProductFamily.objects.filter(name__iexact=family_name)
        if families.exists():
            return families.first()
        
        # Yeni aile oluştur
        slug = SlugService.generate_slug(family_name, ProductFamily)
        family = ProductFamily.objects.create(
            name=family_name,
            slug=slug
        )
        
        logger.info(f"New product family created: {family_name}")
        return family
    
    @staticmethod
    def calculate_profit_margin(price, cost, discount_price=None):
        """
        Kar marjı hesapla.
        
        Args:
            price: Satış fiyatı
            cost: Maliyet
            discount_price: İndirimli fiyat (opsiyonel)
            
        Returns:
            Kar marjı yüzdesi veya None
        """
        try:
            if cost and cost > 0:
                hundred = Decimal('100')
                if discount_price and discount_price > 0:
                    return round(((discount_price - cost) / cost) * hundred, 2)
                return round(((price - cost) / cost) * hundred, 2)
            return None
        except Exception as e:
            logger.error(f"Error calculating profit margin: {str(e)}")
            return None
    
    @staticmethod
    def prepare_product_for_save(product):
        """
        Product kaydını kaydetmeden önce hazırla.
        
        Args:
            product: Product instance
            
        Returns:
            Hazırlanmış Product
        """
        # Slug oluştur
        if not product.slug:
            product.slug = SlugService.generate_slug(product.name, Product, product)
            
        # SKU oluştur (eğer ürün koduna dayalı SKU oluşturma istiyorsanız)
        if not product.sku and product.code:
            product.sku = product.code
            
        return product