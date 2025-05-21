#!/usr/bin/env python
"""
Chunk-based memory-efficient Excel import script.
Processes large Excel files without exceeding memory limits.
"""
import os
import sys
import django
import gc
import pandas as pd
from datetime import datetime
import psutil

# Django setup
sys.path.append('/Users/emreuysal/Documents/Project/VivaCrm v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import transaction, connection, models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from orders.models import Order, OrderItem
from products.models import Product, Category
from customers.models import Customer

User = get_user_model()

class ChunkedExcelReader:
    """Memory-efficient Excel reader that processes files in chunks."""
    
    def __init__(self, file_path: str, chunk_size: int = 1000):
        self.file_path = file_path
        self.chunk_size = chunk_size
        
    def read_chunks(self):
        """Read Excel file in chunks to minimize memory usage."""
        try:
            # Read Excel in chunks using pandas iterator
            for chunk in pd.read_excel(self.file_path, chunksize=self.chunk_size):
                yield chunk
                
        except:
            # Alternative approach if direct chunking fails
            start_row = 0
            while True:
                try:
                    chunk = pd.read_excel(
                        self.file_path,
                        skiprows=start_row,
                        nrows=self.chunk_size,
                        header=0 if start_row == 0 else None
                    )
                    
                    if chunk.empty or len(chunk) == 0:
                        break
                        
                    # If not first chunk, set column names from first chunk
                    if start_row > 0:
                        chunk.columns = self._columns
                    else:
                        self._columns = chunk.columns
                        
                    yield chunk
                    start_row += self.chunk_size
                    
                except Exception as e:
                    if start_row == 0:
                        raise e
                    break

class MemoryEfficientOrderImporter:
    """Memory-efficient order importer using chunked processing."""
    
    def __init__(self, excel_path: str, chunk_size: int = 500):
        self.excel_path = excel_path
        self.chunk_size = chunk_size
        self.stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'created_orders': 0,
            'created_customers': 0,
            'created_products': 0,
            'created_order_items': 0,
            'errors': []
        }
        
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
        
    def log_memory(self, action: str):
        """Log memory usage."""
        memory_mb = self.get_memory_usage()
        print(f"[{datetime.now()}] {action} - Memory: {memory_mb:.1f}MB")
        
    def clear_memory(self):
        """Clear memory and run garbage collection."""
        gc.collect()
        # Clear Django query cache
        connection.queries_log.clear()
        
    def create_product_if_not_exists(self, sku, name, gtin=None):
        """Create product if it doesn't exist."""
        try:
            # Try to find by SKU first
            product = Product.objects.filter(sku=sku).first()
            if product:
                return product
                
            # Try to find by GTIN if provided
            if gtin and pd.notna(gtin):
                gtin_str = str(gtin).replace('.0', '').strip()
                product = Product.objects.filter(barcode=gtin_str).first()
                if product:
                    return product
            
            # Create new product
            category = Category.objects.all().first()
            if not category:
                category = Category.objects.create(
                    name="Genel",
                    slug="genel",
                    is_active=True
                )
            
            product = Product.objects.create(
                name=name[:255],
                code=sku[:50].upper(),
                sku=sku,
                barcode=gtin_str if gtin and pd.notna(gtin) else '',
                category=category,
                price=0,
                stock=0,
                threshold_stock=0,
                description=f"Sipariş import'tan oluşturuldu - {datetime.now()}",
                is_active=True,
                slug=slugify(f"{sku}-{name[:50]}")
            )
            self.stats['created_products'] += 1
            return product
            
        except Exception as e:
            print(f"Product creation error for SKU {sku}: {str(e)}")
            return None
            
    def create_customer_if_not_exists(self, name, phone=None):
        """Create customer if it doesn't exist."""
        try:
            # Try to find existing customer by name or company_name
            customer = Customer.objects.filter(
                models.Q(name__iexact=name) | models.Q(company_name__iexact=name)
            ).first()
            if customer:
                return customer
                
            # Create new customer - determine if corporate or individual
            is_corporate = any(corp_word in name.upper() for corp_word in ['AMAZON', 'INC', 'LLC', 'CORP', 'LTD'])
            
            customer = Customer.objects.create(
                name=name[:255],
                company_name=name[:255] if is_corporate else '',
                type='corporate' if is_corporate else 'individual',
                phone=phone[:20] if phone and pd.notna(phone) else '',
                email='',
                tax_number='',
                tax_office='',
                is_active=True
            )
            self.stats['created_customers'] += 1
            return customer
            
        except Exception as e:
            print(f"Customer creation error for {name}: {str(e)}")
            return None
            
    def process_chunk(self, chunk_df):
        """Process a single chunk of data."""
        self.log_memory(f"Processing chunk with {len(chunk_df)} rows")
        
        created_orders = []
        created_items = []
        
        for _, row in chunk_df.iterrows():
            try:
                # Get order data with correct column names
                order_number = str(row.get('SIPARIŞ NO', '')).strip()
                customer_name = str(row.get('MÜŞTERI ISMI', '')).strip()
                sku = str(row.get('SKU', '')).strip()
                product_name = str(row.get('ÜRÜN ISMI', '')).strip()
                quantity = int(row.get('ADET', 1))
                price = float(row.get('BIRIM FIYAT', 0))
                gtin = row.get('GTIN')
                
                # Skip invalid rows
                if not order_number or not customer_name or not sku:
                    continue
                    
                # Get or create customer
                customer = self.create_customer_if_not_exists(customer_name)
                if not customer:
                    continue
                    
                # Get or create product
                product = self.create_product_if_not_exists(sku, product_name, gtin)
                if not product:
                    continue
                    
                # Find or create order
                order = Order.objects.filter(order_number=order_number).first()
                if not order:
                    order = Order(
                        order_number=order_number,
                        customer=customer,
                        delivery_date=datetime.now(),
                        payment_method='bank_transfer',
                        payment_status='pending',
                        status='pending',
                        subtotal=0,
                        tax_amount=0,
                        total_amount=0
                    )
                    created_orders.append(order)
                    self.stats['created_orders'] += 1
                
                # Create order item
                created_items.append(OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=price,
                    discount_amount=0,
                    tax_rate=0
                ))
                
                self.stats['processed_rows'] += 1
                self.stats['created_order_items'] += 1
                
            except Exception as e:
                self.stats['errors'].append(f"Row {self.stats['total_rows']}: {str(e)}")
                
        # Bulk create orders and items
        if created_orders:
            Order.objects.bulk_create(created_orders, ignore_conflicts=True)
            
        if created_items:
            # Need to refresh order IDs first
            for item in created_items:
                if not item.order.id:
                    item.order = Order.objects.get(order_number=item.order.order_number)
            OrderItem.objects.bulk_create(created_items, ignore_conflicts=True)
            
        # Clear memory after processing
        self.clear_memory()
        self.log_memory("Chunk processed")
        
    def import_orders(self):
        """Import orders from Excel file using chunked processing."""
        print(f"Starting chunked import from: {self.excel_path}")
        self.log_memory("Initial")
        
        try:
            # Use chunked reader
            reader = ChunkedExcelReader(self.excel_path, chunk_size=self.chunk_size)
            
            chunk_number = 0
            for chunk_df in reader.read_chunks():
                chunk_number += 1
                self.stats['total_rows'] += len(chunk_df)
                
                print(f"\nProcessing chunk {chunk_number} ({len(chunk_df)} rows)")
                
                # Process in transaction
                with transaction.atomic():
                    self.process_chunk(chunk_df)
                    
                # Check memory usage
                if self.get_memory_usage() > 400:  # If approaching 500MB limit
                    print("Approaching memory limit, forcing garbage collection...")
                    self.clear_memory()
                    
        except Exception as e:
            print(f"Import error: {str(e)}")
            self.stats['errors'].append(f"Fatal error: {str(e)}")
            
        # Final cleanup
        self.clear_memory()
        self.log_memory("Final")
        
        return self.stats
        
    def print_summary(self):
        """Print import summary."""
        print("\n=== IMPORT SUMMARY ===")
        print(f"Total rows: {self.stats['total_rows']}")
        print(f"Processed rows: {self.stats['processed_rows']}")
        print(f"Created orders: {self.stats['created_orders']}")
        print(f"Created order items: {self.stats['created_order_items']}")
        print(f"Created customers: {self.stats['created_customers']}")
        print(f"Created products: {self.stats['created_products']}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nERRORS:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")


def main():
    excel_path = '/Users/emreuysal/Downloads/siparis_excel_sablonu.xlsx'
    
    # Create importer with small chunk size for memory efficiency
    importer = MemoryEfficientOrderImporter(excel_path, chunk_size=500)
    
    # Import orders
    stats = importer.import_orders()
    
    # Print summary
    importer.print_summary()
    
    print("\nImport completed successfully!")


if __name__ == "__main__":
    main()