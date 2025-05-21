"""
Smart Excel Product Import System - Updated for new template.
Handles category creation, validation errors, memory management, and field corrections.
"""
import os
import gc
import pandas as pd
import numpy as np
from decimal import Decimal
from django.db import transaction
from django.utils.text import slugify
from django.utils import timezone
from datetime import datetime
import logging
import requests
from urllib.parse import urlparse

from products.models import Product, Category, ProductFamily, ProductImage, ProductAttribute, ProductAttributeValue
from core.excel_chunked import MemoryEfficientFileHandler

# Configure logging
logger = logging.getLogger(__name__)


class SmartProductImporter:
    """
    Smart product importer that handles all common issues:
    - Automatic category creation
    - Field validation and correction
    - Memory efficient processing
    - Error recovery and reporting
    - Image URL downloading
    - Attribute handling (Color, Size)
    """
    
    def __init__(self, file_path=None, file_buffer=None, user=None):
        self.file_path = file_path
        self.file_buffer = file_buffer
        self.user = user
        self.errors = []
        self.warnings = []
        self.created_categories = []
        self.created_families = []
        self.created_products = []
        self.updated_products = []
        self.stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'created_products': 0,
            'updated_products': 0,
            'created_categories': 0,
            'created_families': 0,
            'errors': 0,
            'warnings': 0
        }
        
    def process_file(self):
        """Main entry point for processing Excel file."""
        try:
            # Determine file size for memory management
            if self.file_path:
                file_size = os.path.getsize(self.file_path)
            else:
                self.file_buffer.seek(0, 2)
                file_size = self.file_buffer.tell()
                self.file_buffer.seek(0)
                
            # Use chunked processing for large files
            if file_size > 5 * 1024 * 1024:  # 5MB
                return self._process_large_file()
            else:
                return self._process_small_file()
                
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            self.errors.append(f"Import failed: {str(e)}")
            return self._create_result()
            
    def _process_small_file(self):
        """Process small files in memory."""
        try:
            # Read entire file
            df = pd.read_excel(
                self.file_path or self.file_buffer,
                sheet_name=0,
                engine='openpyxl'
            )
            
            self.stats['total_rows'] = len(df)
            
            # Process all rows
            with transaction.atomic():
                for index, row in df.iterrows():
                    self._process_row(row, index + 2)  # +2 for Excel row number
                    
            return self._create_result()
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            self.errors.append(f"File processing error: {str(e)}")
            return self._create_result()
            
    def _process_large_file(self):
        """Process large files in chunks to manage memory."""
        try:
            chunk_size = 500
            chunks_processed = 0
            
            # Process file in chunks
            for chunk_df in pd.read_excel(
                self.file_path or self.file_buffer,
                sheet_name=0,
                engine='openpyxl',
                chunksize=chunk_size
            ):
                chunks_processed += 1
                logger.info(f"Processing chunk {chunks_processed}")
                
                with transaction.atomic():
                    for index, row in chunk_df.iterrows():
                        self._process_row(row, index + 2)
                        
                # Clear memory after each chunk
                gc.collect()
                
            return self._create_result()
            
        except Exception as e:
            logger.error(f"Error processing large file: {str(e)}")
            self.errors.append(f"Large file processing error: {str(e)}")
            return self._create_result()
            
    def _process_row(self, row, row_number):
        """Process a single row from Excel."""
        try:
            # Skip empty rows
            if pd.isna(row.get('URUNISMI')) and pd.isna(row.get('SKU')):
                return
                
            # Extract and validate data
            product_data = self._extract_product_data(row, row_number)
            
            if not product_data:
                return
                
            # Create or update product
            product, created = self._save_product(product_data)
            
            if created:
                self.created_products.append(product)
                self.stats['created_products'] += 1
            else:
                self.updated_products.append(product)
                self.stats['updated_products'] += 1
                
            # Handle product attributes (Color, Size)
            self._save_product_attributes(product, product_data)
            
            # Download and save image if URL provided
            if product_data.get('image_url'):
                self._download_product_image(product, product_data['image_url'])
                
            self.stats['processed_rows'] += 1
            
        except Exception as e:
            logger.error(f"Error processing row {row_number}: {str(e)}")
            self.errors.append(f"Row {row_number}: {str(e)}")
            self.stats['errors'] += 1
            
    def _extract_product_data(self, row, row_number):
        """Extract and validate product data from row."""
        data = {}
        
        # Name (required) - from URUNISMI
        name = row.get('URUNISMI')
        if name and not pd.isna(name):
            data['name'] = str(name).strip()[:255]
        else:
            self.errors.append(f"Row {row_number}: Product name is required")
            return None
            
        # Code (generate if missing) - from SKU
        sku = row.get('SKU')
        if sku and not pd.isna(sku):
            # Clean SKU - remove newlines and strip
            sku_clean = str(sku).strip().replace('\n', '').replace('\r', '')
            data['code'] = sku_clean[:50]
            data['sku'] = sku_clean[:50]
        else:
            data['code'] = self._generate_code(data['name'])
            data['sku'] = data['code']
                
        # Price (required) - from FIYAT
        price = row.get('FIYAT')
        if price is not None and not pd.isna(price):
            try:
                # Django Decimal field için doğrudan Decimal kullan
                from decimal import Decimal, ROUND_HALF_UP
                price_str = f"{float(price):.2f}"  # İki ondalık basamağa format
                data['price'] = Decimal(price_str)
            except:
                self.errors.append(f"Row {row_number}: Invalid price format")
                return None
        else:
            self.errors.append(f"Row {row_number}: Price is required")
            return None
            
        # Category (create if not exists) - from KATEGORI
        category = row.get('KATEGORI')
        if category and not pd.isna(category):
            category_name = str(category).strip()
            data['category'] = self._get_or_create_category(category_name)
        else:
            data['category'] = self._get_default_category()
            
        # Product Family (create if not exists) - from URUNAILESI
        family = row.get('URUNAILESI')
        if family and not pd.isna(family):
            # Clean family name - handle multiline strings
            family_name = str(family).strip().replace('\n', ' ').replace('\r', ' ')
            # Remove extra quotes
            family_name = family_name.strip('"').strip("'")
            data['family'] = self._get_or_create_family(family_name)
            
        # Cost - from URUNMALIYETI
        cost = row.get('URUNMALIYETI')
        if cost is not None and not pd.isna(cost):
            try:
                # Convert comma to dot for decimal
                cost_str = str(cost).replace(',', '.')
                # Django Decimal field için doğrudan Decimal kullan
                from decimal import Decimal
                cost_str = f"{float(cost_str):.2f}"  # İki ondalık basamağa format
                data['cost'] = Decimal(cost_str)
            except:
                pass
                
        # Shipping Cost - from KARGOMALIYET  
        shipping_cost = row.get('KARGOMALIYET')
        if shipping_cost is not None and not pd.isna(shipping_cost):
            try:
                # Convert comma to dot for decimal
                shipping_str = str(shipping_cost).replace(',', '.')
                shipping_decimal = Decimal(f"{float(shipping_str):.2f}")
                # Store as extra data or custom field
                data['shipping_cost'] = shipping_decimal
            except:
                pass
                
        # Commission - from KOMISYON
        commission = row.get('KOMISYON')
        if commission is not None and not pd.isna(commission):
            try:
                # Convert comma to dot for decimal
                commission_str = str(commission).replace(',', '.')
                commission_decimal = Decimal(f"{float(commission_str):.2f}")
                # Store as extra data or custom field
                data['commission'] = commission_decimal
            except:
                pass
                
        # Barcode - from BARKOD
        barcode = row.get('BARKOD')
        if barcode and not pd.isna(barcode):
            data['barcode'] = str(barcode).replace('.0', '').strip()[:50]
            
        # ASIN
        asin = row.get('ASIN')
        if asin and not pd.isna(asin):
            data['asin'] = str(asin).strip()[:50]
            
        # Color - from RENK (for attributes)
        color = row.get('RENK')
        if color and not pd.isna(color):
            data['color'] = str(color).strip()
            
        # Size - from BOYUT (for attributes) 
        size = row.get('BOYUT')
        if size and not pd.isna(size):
            data['size'] = str(size).strip()
            
        # Image URL - from GORSELURL
        image_url = row.get('GORSELURL')
        if image_url and not pd.isna(image_url):
            data['image_url'] = str(image_url).strip()
            
        # Default stock to 0 since not in template
        data['stock'] = 0
        
        # Set default tax rate
        data['tax_rate'] = 18
        
        return data
        
    def _generate_code(self, name):
        """Generate product code from name."""
        # Create code from name
        code = slugify(name[:30]).upper().replace('-', '_')
        
        # Make unique
        base_code = code
        counter = 1
        while Product.objects.filter(code=code).exists():
            code = f"{base_code}_{counter}"
            counter += 1
            
        return code[:50]
        
    def _get_or_create_category(self, name):
        """Get or create category by name."""
        if not name or name.lower() == 'nan':
            return self._get_default_category()
            
        # Clean category name
        name = name.strip()
        
        # Try to find existing category
        category = Category.objects.filter(name__iexact=name).first()
        if category:
            return category
            
        # Create new category
        try:
            category = Category.objects.create(
                name=name[:100],
                slug=slugify(name[:100]),
                description=f"Excel import'tan otomatik oluşturuldu - {datetime.now()}",
                is_active=True
            )
            self.created_categories.append(category)
            self.stats['created_categories'] += 1
            logger.info(f"Created category: {name}")
            return category
            
        except Exception as e:
            logger.error(f"Error creating category {name}: {str(e)}")
            return self._get_default_category()
            
    def _get_or_create_family(self, name):
        """Get or create product family by name."""
        if not name or name.lower() == 'nan':
            return None
            
        # Clean family name - remove extra whitespace
        name = ' '.join(name.split())
        
        # Try to find existing family
        family = ProductFamily.objects.filter(name__iexact=name).first()
        if family:
            return family
            
        # Create new family
        try:
            family = ProductFamily.objects.create(
                name=name[:255],
                slug=slugify(name[:255]),
                description=f"Excel import'tan otomatik oluşturuldu - {datetime.now()}",
                is_active=True
            )
            self.created_families.append(family)
            self.stats['created_families'] += 1
            logger.info(f"Created product family: {name}")
            return family
            
        except Exception as e:
            logger.error(f"Error creating family {name}: {str(e)}")
            return None
            
    def _get_default_category(self):
        """Get or create default category."""
        category, created = Category.objects.get_or_create(
            slug='genel',
            defaults={
                'name': 'Genel',
                'description': 'Varsayılan kategori',
                'is_active': True
            }
        )
        if created:
            self.created_categories.append(category)
            self.stats['created_categories'] += 1
        return category
        
    def _save_product(self, data):
        """Save product to database."""
        try:
            # Generate unique slug
            base_slug = slugify(data['name'][:200])
            slug = base_slug
            counter = 1
            
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            # Set defaults with correct decimal handling
            defaults = {
                'name': data['name'],
                'slug': slug,
                'price': data['price'],
                'category': data['category'],
                'family': data.get('family'),
                'stock': data.get('stock', 0),
                'sku': data.get('sku', ''),
                'barcode': data.get('barcode', ''),
                'asin': data.get('asin', ''),
                'description': data.get('description', ''),
                'cost': data.get('cost'),
                'tax_rate': data.get('tax_rate', 18),
                'is_active': True
            }
            
            # Check if product exists
            existing_product = Product.objects.filter(code=data['code']).first()
            
            if existing_product:
                # Update existing product
                for key, value in defaults.items():
                    setattr(existing_product, key, value)
                existing_product.save()
                return existing_product, False
            else:
                # Create new product with direct database insert to avoid validation
                product = Product.objects.create(**{'code': data['code'], **defaults})
                return product, True
            
        except Exception as e:
            logger.error(f"Error saving product: {str(e)}")
            if 'Validation error' in str(e):
                logger.error(f"Validation error in Product save: {e}")
            raise
        
    def _save_product_attributes(self, product, data):
        """Save product attributes like color and size."""
        # Handle color attribute
        if data.get('color'):
            color_attr, _ = ProductAttribute.objects.get_or_create(
                slug='color',
                defaults={'name': 'Renk', 'description': 'Ürün rengi'}
            )
            
            ProductAttributeValue.objects.update_or_create(
                product=product,
                attribute=color_attr,
                defaults={'value': data['color']}
            )
            
        # Handle size attribute
        if data.get('size'):
            size_attr, _ = ProductAttribute.objects.get_or_create(
                slug='size',
                defaults={'name': 'Boyut', 'description': 'Ürün boyutu'}
            )
            
            ProductAttributeValue.objects.update_or_create(
                product=product,
                attribute=size_attr,
                defaults={'value': data['size']}
            )
            
    def _download_product_image(self, product, image_url):
        """Download and save product image from URL."""
        try:
            # Check if URL is valid
            parsed_url = urlparse(image_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.warning(f"Invalid image URL: {image_url}")
                return
                
            # Don't download images in test mode
            if os.environ.get('DJANGO_SETTINGS_MODULE') == 'core.settings':
                logger.info(f"Skipping image download in test mode: {image_url}")
                return
                
            # Download image
            response = requests.get(image_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # Generate filename
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"{product.slug}.jpg"
                
            # Create ProductImage with content
            from django.core.files.base import ContentFile
            
            image = ProductImage(
                product=product,
                alt_text=product.name,
                is_primary=not product.images.exists()  # First image is primary
            )
            
            # Save image file first, then save the model
            image.image.save(filename, ContentFile(response.content), save=False)
            image.save()
            
            logger.info(f"Downloaded image for product {product.code}")
            
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {str(e)}")
        
    def _create_result(self):
        """Create import result."""
        return {
            'success': self.stats['errors'] == 0,
            'stats': self.stats,
            'errors': self.errors,
            'warnings': self.warnings,
            'created_products': self.created_products,
            'updated_products': self.updated_products,
            'created_categories': self.created_categories,
            'created_families': self.created_families
        }


# Main import function to be called from views
def import_products_smart(file_path=None, file_buffer=None, user=None, show_warnings=True):
    """
    Main function to import products from Excel with all smart features.
    
    Args:
        file_path: Path to Excel file
        file_buffer: File buffer (for uploaded files)
        user: User performing the import
        show_warnings: Whether to show warnings (default True)
        
    Returns:
        Import result dictionary
    """
    importer = SmartProductImporter(
        file_path=file_path,
        file_buffer=file_buffer,
        user=user
    )
    
    result = importer.process_file()
    
    # Remove warnings if requested
    if not show_warnings:
        result['warnings'] = []
        
    return result