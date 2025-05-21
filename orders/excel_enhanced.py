"""
Enhanced Excel import/export functionality for the Orders app with ImportTask integration.
"""
import pandas as pd
import uuid
import logging
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from django.utils import timezone
from django.db import transaction
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)

from .models import Order, OrderItem
from customers.models import Customer, Address
from products.models import Product
from core.models_import import ImportTask, ImportSummary, DetailedImportResult
from .excel import generate_order_number, generate_order_template


class EnhancedOrderExcelImport:
    """Enhanced order import with detailed logging and error tracking"""
    
    def __init__(self, file_obj, user=None, update_existing=False):
        self.file_obj = file_obj
        self.user = user
        self.update_existing = update_existing
        self.import_task = None
        
    def create_import_task(self, file_name):
        """Create ImportTask record for tracking"""
        self.import_task = ImportTask.objects.create(
            type='order',
            status='pending',
            file_name=file_name,
            file_path='',
            created_by=self.user,
            progress=0
        )
        return self.import_task
        
    def update_progress(self, progress):
        """Update import task progress"""
        if self.import_task:
            self.import_task.progress = progress
            self.import_task.save(update_fields=['progress'])
    
    def log_import_result(self, row_number, data, status, error_message=None, error_details=None):
        """Log detailed import result for each row"""
        if self.import_task:
            DetailedImportResult.objects.create(
                import_task=self.import_task,
                row_number=row_number,
                data=data,
                status=status,
                error_message=error_message,
                error_details=error_details
            )
    
    def create_or_update_customer(self, row_data):
        """Create or update customer with better error handling"""
        customer_name = row_data.get("MÜŞTERI ISMI", "").strip()
        
        if not customer_name:
            raise ValueError("Müşteri ismi zorunludur")
        
        # Try to find existing customer
        customer = Customer.objects.filter(name__iexact=customer_name).first()
        
        if not customer:
            # Create email from customer name
            import re
            email_name = re.sub(r'[^\w\s]', '', customer_name.lower())
            email_name = re.sub(r'\s+', '.', email_name.strip())
            if not email_name:
                email_name = "customer"
            
            # Create new customer
            customer = Customer.objects.create(
                name=customer_name,
                email=f"{email_name}@example.com",
                phone="",
                company_name="",
                notes=f"Auto-created from Excel import"
            )
            
            # Create address if location data available
            if row_data.get('ŞEHIR') or row_data.get('EYALET'):
                Address.objects.create(
                    customer=customer,
                    title="Primary Address",
                    type="shipping",
                    city=row_data.get('ŞEHIR', ''),
                    state=row_data.get('EYALET', ''),
                    address_line1="Excel import",
                    country="Türkiye",
                    is_default=True
                )
        
        return customer
    
    def find_or_create_product(self, row_data):
        """Find or create product with GTIN handling"""
        sku = str(row_data.get("SKU", "")).strip()
        product_name = row_data.get("ÜRÜN ISMI", "").strip()
        
        if not sku or not product_name:
            raise ValueError("SKU ve ürün ismi zorunludur")
        
        # First try to find by SKU
        product = Product.objects.filter(sku=sku).first()
        
        if not product and row_data.get("GTIN"):
            # Try to find by GTIN/barcode
            gtin_raw = row_data.get("GTIN")
            if isinstance(gtin_raw, float):
                gtin_value = str(int(gtin_raw))
            else:
                gtin_value = str(gtin_raw)
            
            product = Product.objects.filter(barcode=gtin_value).first()
        
        if not product:
            # Create new product
            gtin_value = ""
            if row_data.get("GTIN"):
                gtin_raw = row_data.get("GTIN")
                if isinstance(gtin_raw, float):
                    gtin_value = str(int(gtin_raw))
                else:
                    gtin_value = str(gtin_raw)
            
            # Parse unit price
            unit_price_str = str(row_data.get("BIRIM FIYAT", "0")).replace(',', '.')
            try:
                unit_price = Decimal(unit_price_str)
            except InvalidOperation:
                unit_price = Decimal("0")
            
            product = Product.objects.create(
                name=product_name,
                sku=sku,
                barcode=gtin_value,
                description="Auto-created from Excel import",
                price=unit_price,
                discount_price=0,
                tax_rate=18,
                stock=100,
                is_active=True,
                code=sku
            )
        
        return product
    
    def import_data(self):
        """Main import method with transaction management"""
        try:
            # Read Excel file
            df = pd.read_excel(self.file_obj)
            
            # Create import task
            file_name = getattr(self.file_obj, 'name', 'order_import.xlsx')
            self.create_import_task(file_name)
            
            # Update status to processing
            self.import_task.status = 'processing'
            self.import_task.started_at = timezone.now()
            self.import_task.save()
            
            # Initialize summary
            summary = ImportSummary.objects.create(
                import_task=self.import_task,
                total_rows=len(df),
                successful_rows=0,
                failed_rows=0,
                updated_rows=0,
                skipped_rows=0
            )
            
            # Group by order number
            order_groups = df.groupby("SIPARIŞ NO")
            total_groups = len(order_groups)
            
            # Process each order
            for idx, (order_number, order_group) in enumerate(order_groups):
                progress = int((idx / total_groups) * 100)
                self.update_progress(progress)
                
                try:
                    with transaction.atomic():
                        # Process order creation/update
                        first_row = order_group.iloc[0]
                        row_num = first_row.name + 2  # Excel row number
                        
                        # Create/update customer
                        customer = self.create_or_update_customer(first_row.to_dict())
                        
                        # Check if order exists
                        existing_order = Order.objects.filter(order_number=order_number).first()
                        
                        # Parse order date
                        order_date_str = first_row["SIPARIŞ TARIHI VE SAATI"]
                        try:
                            order_date = pd.to_datetime(order_date_str, format="%d.%m.%Y %H:%M")
                        except:
                            order_date = timezone.now()
                        
                        # Create or update order
                        if existing_order and self.update_existing:
                            order = existing_order
                            order.customer = customer
                            order.order_date = order_date
                            order.save()
                            
                            # Clear existing items
                            order.items.all().delete()
                            
                            status = 'updated'
                            summary.updated_rows += 1
                        else:
                            # Create new order
                            order = Order.objects.create(
                                order_number=order_number,
                                customer=customer,
                                status='pending',
                                payment_status='pending',
                                order_date=order_date,
                                notes=f"Imported from {file_name}",
                                owner=None
                            )
                            status = 'created'
                            summary.successful_rows += 1
                        
                        # Process order items
                        for item_idx, item_row in order_group.iterrows():
                            item_row_num = item_idx + 2
                            
                            try:
                                # Find/create product
                                product = self.find_or_create_product(item_row.to_dict())
                                
                                # Parse quantity and prices
                                quantity = int(item_row["ADET"])
                                unit_price = Decimal(str(item_row["BIRIM FIYAT"]).replace(',', '.'))
                                
                                discount_amount = Decimal("0")
                                if item_row.get("BIRIM INDIRIM"):
                                    try:
                                        discount_amount = Decimal(str(item_row["BIRIM INDIRIM"]).replace(',', '.'))
                                    except:
                                        pass
                                
                                # Create order item
                                OrderItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=quantity,
                                    unit_price=unit_price,
                                    discount_amount=discount_amount,
                                    tax_rate=product.tax_rate
                                )
                                
                                # Log success
                                self.log_import_result(
                                    row_number=item_row_num,
                                    data=item_row.to_dict(),
                                    status='created'
                                )
                                
                            except Exception as e:
                                # Log item error
                                self.log_import_result(
                                    row_number=item_row_num,
                                    data=item_row.to_dict(),
                                    status='failed',
                                    error_message=str(e),
                                    error_details={'type': 'order_item_error'}
                                )
                                summary.failed_rows += 1
                        
                        # Calculate order totals
                        order.calculate_totals()
                        
                        # Log order success
                        self.log_import_result(
                            row_number=row_num,
                            data=first_row.to_dict(),
                            status=status
                        )
                        
                except Exception as e:
                    # Log order error
                    self.log_import_result(
                        row_number=row_num,
                        data=first_row.to_dict(),
                        status='failed',
                        error_message=str(e),
                        error_details={'type': 'order_error'}
                    )
                    summary.failed_rows += 1
            
            # Update import task completion
            self.import_task.status = 'completed' if summary.failed_rows == 0 else 'partial'
            self.import_task.progress = 100
            self.import_task.completed_at = timezone.now()
            self.import_task.save()
            
            # Save final summary
            summary.save()
            
            # Get error rows for backward compatibility
            error_rows = []
            failed_results = DetailedImportResult.objects.filter(
                import_task=self.import_task,
                status='failed'
            )
            
            for result in failed_results:
                error_rows.append({
                    'row': result.row_number,
                    'error': result.error_message
                })
            
            return {
                'total': summary.total_rows,
                'created': summary.successful_rows,
                'updated': summary.updated_rows,
                'error_count': summary.failed_rows,
                'error_rows': error_rows,
                'import_task_id': self.import_task.id
            }
            
        except Exception as e:
            # Log critical error
            if self.import_task:
                self.import_task.status = 'failed'
                self.import_task.error_message = str(e)
                self.import_task.completed_at = timezone.now()
                self.import_task.save()
            
            logger.error(f"Critical import error: {str(e)}")
            raise


def enhanced_import_orders_excel(file_obj, user=None, update_existing=False):
    """Enhanced import function with ImportTask integration"""
    importer = EnhancedOrderExcelImport(file_obj, user, update_existing)
    return importer.import_data()