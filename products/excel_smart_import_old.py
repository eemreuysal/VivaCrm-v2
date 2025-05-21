"""
Smart Excel Product Import System - All-in-one solution for product imports.
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

from products.models import Product, Category, ProductFamily
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
    """
    
    def __init__(self, file_path=None, file_buffer=None, user=None):
        self.file_path = file_path
        self.file_buffer = file_buffer
        self.user = user
        self.errors = []
        self.warnings = []
        self.created_categories = []
        self.created_products = []
        self.updated_products = []
        self.stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'created_products': 0,
            'updated_products': 0,
            'created_categories': 0,
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
            if pd.isna(row.get(self._find_column(row, ['name', 'ürün adı', 'ürün ismi']))):
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
                
            self.stats['processed_rows'] += 1
            
        except Exception as e:
            logger.error(f"Error processing row {row_number}: {str(e)}")
            self.errors.append(f"Row {row_number}: {str(e)}")
            self.stats['errors'] += 1
            
    def _extract_product_data(self, row, row_number):
        """Extract and validate product data from row."""
        data = {}
        
        # Name (required)
        name_col = self._find_column(row, ['name', 'ürün adı', 'ürün ismi', 'product name'])
        if name_col:
            name = str(row[name_col]).strip()
            if not name or name.lower() == 'nan':
                self.errors.append(f"Row {row_number}: Product name is required")
                return None
            data['name'] = name[:255]
        else:
            self.errors.append(f"Row {row_number}: Product name column not found")
            return None
            
        # Code (generate if missing)
        code_col = self._find_column(row, ['code', 'kod', 'ürün kodu', 'product code'])
        if code_col and not pd.isna(row[code_col]):
            data['code'] = str(row[code_col]).strip()[:50]
        else:
            # Generate from name or SKU
            sku_col = self._find_column(row, ['sku', 'stok kodu'])
            if sku_col and not pd.isna(row[sku_col]):
                data['code'] = str(row[sku_col]).strip()[:50]
            else:
                data['code'] = self._generate_code(data['name'])
                
        # Price (required)
        price_col = self._find_column(row, ['price', 'fiyat', 'birim fiyat', 'unit price'])
        if price_col and not pd.isna(row[price_col]):
            try:
                price = float(str(row[price_col]).replace(',', '.'))
                data['price'] = round(price, 2)
            except:
                self.errors.append(f"Row {row_number}: Invalid price format")
                return None
        else:
            self.errors.append(f"Row {row_number}: Price is required")
            return None
            
        # Category (create if not exists)
        category_col = self._find_column(row, ['category', 'kategori', 'category name'])
        if category_col and not pd.isna(row[category_col]):
            category_name = str(row[category_col]).strip()
            data['category'] = self._get_or_create_category(category_name)
        else:
            data['category'] = self._get_default_category()
            
        # Optional fields
        data.update(self._extract_optional_fields(row))
        
        return data
        
    def _extract_optional_fields(self, row):
        """Extract optional fields from row."""
        data = {}
        
        # Stock
        stock_col = self._find_column(row, ['stock', 'stok', 'quantity', 'miktar'])
        if stock_col and not pd.isna(row[stock_col]):
            try:
                data['stock'] = int(float(str(row[stock_col])))
            except:
                data['stock'] = 0
        else:
            data['stock'] = 0
            
        # SKU
        sku_col = self._find_column(row, ['sku', 'stok kodu'])
        if sku_col and not pd.isna(row[sku_col]):
            data['sku'] = str(row[sku_col]).strip()[:50]
            
        # Barcode
        barcode_col = self._find_column(row, ['barcode', 'barkod', 'gtin', 'ean'])
        if barcode_col and not pd.isna(row[barcode_col]):
            data['barcode'] = str(row[barcode_col]).replace('.0', '').strip()[:50]
            
        # Description
        desc_col = self._find_column(row, ['description', 'açıklama', 'desc'])
        if desc_col and not pd.isna(row[desc_col]):
            data['description'] = str(row[desc_col]).strip()
            
        # Cost
        cost_col = self._find_column(row, ['cost', 'maliyet'])
        if cost_col and not pd.isna(row[cost_col]):
            try:
                cost = float(str(row[cost_col]).replace(',', '.'))
                data['cost'] = round(cost, 2)
            except:
                pass
                
        # Discount price
        discount_col = self._find_column(row, ['discount_price', 'indirimli fiyat', 'sale price'])
        if discount_col and not pd.isna(row[discount_col]):
            try:
                discount = float(str(row[discount_col]).replace(',', '.'))
                data['discount_price'] = round(discount, 2)
            except:
                pass
                
        return data
        
    def _find_column(self, row, possible_names):
        """Find column by possible names (case insensitive)."""
        if isinstance(row, pd.Series):
            columns = row.index
        else:
            columns = row.keys()
            
        for col in columns:
            if str(col).lower() in [name.lower() for name in possible_names]:
                return col
        return None
        
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
        # Generate unique slug
        base_slug = slugify(data['name'][:200])
        slug = base_slug
        counter = 1
        
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        # Set defaults
        defaults = {
            'name': data['name'],
            'slug': slug,
            'price': data['price'],
            'category': data['category'],
            'stock': data.get('stock', 0),
            'sku': data.get('sku', ''),
            'barcode': data.get('barcode', ''),
            'description': data.get('description', ''),
            'cost': data.get('cost'),
            'discount_price': data.get('discount_price'),
            'is_active': True
        }
        
        # Create or update
        product, created = Product.objects.update_or_create(
            code=data['code'],
            defaults=defaults
        )
        
        return product, created
        
    def _create_result(self):
        """Create import result."""
        return {
            'success': self.stats['errors'] == 0,
            'stats': self.stats,
            'errors': self.errors,
            'warnings': self.warnings,
            'created_products': self.created_products,
            'updated_products': self.updated_products,
            'created_categories': self.created_categories
        }


# Main import function to be called from views
def import_products_smart(file_path=None, file_buffer=None, user=None):
    """
    Main function to import products from Excel with all smart features.
    
    Args:
        file_path: Path to Excel file
        file_buffer: File buffer (for uploaded files)
        user: User performing the import
        
    Returns:
        Import result dictionary
    """
    importer = SmartProductImporter(
        file_path=file_path,
        file_buffer=file_buffer,
        user=user
    )
    
    return importer.process_file()