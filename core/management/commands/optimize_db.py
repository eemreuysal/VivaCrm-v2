"""
Management command to optimize database performance.
"""
import time
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.apps import apps
from django.conf import settings
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize database performance by adding indexes and running ANALYZE'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only run ANALYZE without adding indexes',
        )
        
        parser.add_argument(
            '--indexes-only',
            action='store_true',
            help='Only add missing indexes without running ANALYZE',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show SQL statements without executing them',
        )
    
    def handle(self, *args, **options):
        analyze_only = options['analyze_only']
        indexes_only = options['indexes_only']
        dry_run = options['dry_run']
        
        if analyze_only and indexes_only:
            raise CommandError("Cannot specify both --analyze-only and --indexes-only")
        
        # Start timing
        start_time = time.time()
        
        # Log start
        if dry_run:
            self.stdout.write(self.style.WARNING("Running in dry-run mode - no changes will be made"))
        
        self.stdout.write(self.style.SUCCESS("Starting database optimization..."))
        
        # Add indexes
        if not analyze_only:
            self._add_missing_indexes(dry_run)
        
        # Analyze database
        if not indexes_only:
            self._analyze_database(dry_run)
        
        # Log finish
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f"Database optimization completed in {elapsed_time:.2f} seconds"
        ))
    
    def _add_missing_indexes(self, dry_run):
        """
        Add missing indexes to improve query performance.
        """
        self.stdout.write("Adding missing indexes...")
        
        # Get database engine
        engine = settings.DATABASES['default']['ENGINE']
        is_sqlite = 'sqlite' in engine
        is_postgresql = 'postgresql' in engine
        
        # Define indexes to add for each model
        indexes = self._get_indexes_to_add(is_sqlite, is_postgresql)
        
        # Execute SQL to add indexes
        with connection.cursor() as cursor:
            for table_name, index_commands in indexes.items():
                for index_name, index_sql in index_commands.items():
                    self.stdout.write(f"  Adding index {index_name} to {table_name}")
                    self.stdout.write(f"    SQL: {index_sql}")
                    
                    if not dry_run:
                        try:
                            cursor.execute(index_sql)
                            self.stdout.write(self.style.SUCCESS(f"    Added index {index_name}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"    Error adding index: {str(e)}"))
    
    def _get_indexes_to_add(self, is_sqlite, is_postgresql):
        """
        Get a dictionary of indexes to add for each table.
        """
        indexes = {}
        
        # Helper function to format index SQL
        def get_index_sql(table_name, column_names, index_name=None, unique=False):
            if not index_name:
                index_name = f"idx_{table_name}_{'_'.join(column_names)}"
            
            unique_str = "UNIQUE " if unique else ""
            columns_str = ", ".join(column_names)
            
            if is_sqlite:
                return f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
            elif is_postgresql:
                return f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
            else:
                # Default MySQL syntax
                return f"CREATE {unique_str}INDEX {index_name} ON {table_name} ({columns_str})"
        
        # Customer model indexes
        indexes['customers_customer'] = {
            'idx_customer_owner': get_index_sql('customers_customer', ['owner_id']),
            'idx_customer_active': get_index_sql('customers_customer', ['is_active']),
            'idx_customer_type': get_index_sql('customers_customer', ['type']),
            'idx_customer_name': get_index_sql('customers_customer', ['name']),
            'idx_customer_company': get_index_sql('customers_customer', ['company_name']),
            'idx_customer_created': get_index_sql('customers_customer', ['created_at']),
        }
        
        # Address model indexes
        indexes['customers_address'] = {
            'idx_address_customer': get_index_sql('customers_address', ['customer_id']),
            'idx_address_type': get_index_sql('customers_address', ['type']),
            'idx_address_default': get_index_sql('customers_address', ['is_default']),
        }
        
        # Contact model indexes
        indexes['customers_contact'] = {
            'idx_contact_customer': get_index_sql('customers_contact', ['customer_id']),
            'idx_contact_primary': get_index_sql('customers_contact', ['is_primary']),
        }
        
        # Product model indexes
        indexes['products_product'] = {
            'idx_product_category': get_index_sql('products_product', ['category_id']),
            'idx_product_status': get_index_sql('products_product', ['status']),
            'idx_product_name': get_index_sql('products_product', ['name']),
            'idx_product_current_stock': get_index_sql('products_product', ['current_stock']),
            'idx_product_threshold': get_index_sql('products_product', ['threshold_stock']),
            'idx_product_code_unique': get_index_sql('products_product', ['code'], unique=True),
            'idx_product_sku': get_index_sql('products_product', ['sku']),
        }
        
        # Category model indexes
        indexes['products_category'] = {
            'idx_category_parent': get_index_sql('products_category', ['parent_id']),
            'idx_category_name': get_index_sql('products_category', ['name']),
        }
        
        # StockMovement model indexes
        indexes['products_stockmovement'] = {
            'idx_stockmovement_product': get_index_sql('products_stockmovement', ['product_id']),
            'idx_stockmovement_type': get_index_sql('products_stockmovement', ['movement_type']),
            'idx_stockmovement_created': get_index_sql('products_stockmovement', ['created_at']),
            'idx_stockmovement_created_by': get_index_sql('products_stockmovement', ['created_by_id']),
        }
        
        # Order model indexes
        indexes['orders_order'] = {
            'idx_order_customer': get_index_sql('orders_order', ['customer_id']),
            'idx_order_status': get_index_sql('orders_order', ['status']),
            'idx_order_payment_status': get_index_sql('orders_order', ['payment_status']),
            'idx_order_created': get_index_sql('orders_order', ['created_at']),
            'idx_order_number_unique': get_index_sql('orders_order', ['order_number'], unique=True),
            'idx_order_owner': get_index_sql('orders_order', ['owner_id']),
        }
        
        # OrderItem model indexes
        indexes['orders_orderitem'] = {
            'idx_orderitem_order': get_index_sql('orders_orderitem', ['order_id']),
            'idx_orderitem_product': get_index_sql('orders_orderitem', ['product_id']),
        }
        
        # Payment model indexes
        indexes['orders_payment'] = {
            'idx_payment_order': get_index_sql('orders_payment', ['order_id']),
            'idx_payment_method': get_index_sql('orders_payment', ['payment_method']),
            'idx_payment_date': get_index_sql('orders_payment', ['payment_date']),
        }
        
        # Invoice model indexes
        indexes['invoices_invoice'] = {
            'idx_invoice_customer': get_index_sql('invoices_invoice', ['customer_id']),
            'idx_invoice_order': get_index_sql('invoices_invoice', ['order_id']),
            'idx_invoice_date': get_index_sql('invoices_invoice', ['invoice_date']),
            'idx_invoice_due_date': get_index_sql('invoices_invoice', ['due_date']),
            'idx_invoice_paid': get_index_sql('invoices_invoice', ['is_paid']),
            'idx_invoice_number_unique': get_index_sql('invoices_invoice', ['invoice_number'], unique=True),
        }
        
        # InvoiceItem model indexes
        indexes['invoices_invoiceitem'] = {
            'idx_invoiceitem_invoice': get_index_sql('invoices_invoiceitem', ['invoice_id']),
            'idx_invoiceitem_product': get_index_sql('invoices_invoiceitem', ['product_id']),
        }
        
        return indexes
    
    def _analyze_database(self, dry_run):
        """
        Run ANALYZE on database tables to optimize query plans.
        """
        self.stdout.write("Analyzing database tables...")
        
        # Get database engine
        engine = settings.DATABASES['default']['ENGINE']
        is_sqlite = 'sqlite' in engine
        is_postgresql = 'postgresql' in engine
        
        # Execute appropriate ANALYZE command based on database engine
        with connection.cursor() as cursor:
            try:
                if is_sqlite:
                    analyze_sql = "ANALYZE"
                    self.stdout.write(f"  Running: {analyze_sql}")
                    if not dry_run:
                        cursor.execute(analyze_sql)
                        
                elif is_postgresql:
                    # Get all app models to analyze
                    app_models = []
                    for app_config in apps.get_app_configs():
                        if app_config.name.startswith('django.') or app_config.name == 'admin':
                            continue
                        app_models.extend(app_config.get_models())
                    
                    # Analyze each table
                    for model in app_models:
                        table_name = model._meta.db_table
                        analyze_sql = f"ANALYZE {table_name}"
                        self.stdout.write(f"  Running: {analyze_sql}")
                        if not dry_run:
                            cursor.execute(analyze_sql)
                
                else:
                    # MySQL/MariaDB
                    analyze_sql = "ANALYZE TABLE "
                    tables = []
                    for app_config in apps.get_app_configs():
                        if app_config.name.startswith('django.') or app_config.name == 'admin':
                            continue
                        for model in app_config.get_models():
                            tables.append(model._meta.db_table)
                    
                    if tables:
                        analyze_sql += ", ".join(tables)
                        self.stdout.write(f"  Running: {analyze_sql}")
                        if not dry_run:
                            cursor.execute(analyze_sql)
                
                self.stdout.write(self.style.SUCCESS("  Database analysis completed"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error analyzing database: {str(e)}"))
                
            # Vacuum database if SQLite
            if is_sqlite and not dry_run:
                try:
                    self.stdout.write("  Vacuuming SQLite database...")
                    cursor.execute("VACUUM")
                    self.stdout.write(self.style.SUCCESS("  Vacuum completed"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error vacuuming database: {str(e)}"))