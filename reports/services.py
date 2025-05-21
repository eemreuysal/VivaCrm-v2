from django.db.models import Sum, Count, Avg, Q, F, ExpressionWrapper, DecimalField, DateTimeField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from datetime import timedelta, datetime, time

from customers.models import Customer
from products.models import Product, Category
from orders.models import Order, OrderItem, Payment, Shipment


class ReportService:
    """
    Service class to generate various reports.
    """
    
    @staticmethod
    def get_sales_summary(start_date=None, end_date=None, status=None):
        """
        Get sales summary statistics.
        """
        # Default to last 30 days if no date range specified
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        else:
            # If only date is provided, combine with time to make timezone-aware
            if not isinstance(start_date, datetime):
                start_date = timezone.make_aware(datetime.combine(start_date, time.min))
            
        if not end_date:
            end_date = timezone.now()
        else:
            # If only date is provided, combine with time to make timezone-aware
            if not isinstance(end_date, datetime):
                end_date = timezone.make_aware(datetime.combine(end_date, time.max))
            
        # Base query
        orders = Order.objects.filter(
            order_date__gte=start_date,
            order_date__lte=end_date
        )
        
        # Filter by status if specified
        if status:
            orders = orders.filter(status=status)
            
        # Aggregate data
        summary = {
            'order_count': orders.count(),
            'total_revenue': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'avg_order_value': orders.aggregate(avg=Avg('total_amount'))['avg'] or 0,
            'completed_orders': orders.filter(status='completed').count(),
            'cancelled_orders': orders.filter(status='cancelled').count(),
        }
        
        # Calculate more metrics
        if summary['order_count'] > 0:
            summary['completion_rate'] = (summary['completed_orders'] / summary['order_count']) * 100
            summary['cancellation_rate'] = (summary['cancelled_orders'] / summary['order_count']) * 100
        else:
            summary['completion_rate'] = 0
            summary['cancellation_rate'] = 0
            
        return summary
    
    @staticmethod
    def get_sales_by_period(period='month', start_date=None, end_date=None, status=None):
        """
        Get sales data grouped by time period (day, week, month).
        """
        # Default to last 12 months if no date range specified
        if not start_date:
            if period == 'day':
                start_date = timezone.now() - timedelta(days=30)
            elif period == 'week':
                start_date = timezone.now() - timedelta(weeks=12)
            else:  # month
                start_date = timezone.now() - timedelta(days=365)
        else:
            # If only date is provided, combine with time to make timezone-aware
            if not isinstance(start_date, datetime):
                start_date = timezone.make_aware(datetime.combine(start_date, time.min))
                
        if not end_date:
            end_date = timezone.now()
        else:
            # If only date is provided, combine with time to make timezone-aware
            if not isinstance(end_date, datetime):
                end_date = timezone.make_aware(datetime.combine(end_date, time.max))
            
        # Base query
        orders = Order.objects.filter(
            order_date__gte=start_date,
            order_date__lte=end_date
        )
        
        # Filter by status if specified
        if status:
            orders = orders.filter(status=status)
            
        # Group by period
        if period == 'day':
            truncated_date = TruncDay('order_date')
        elif period == 'week':
            truncated_date = TruncWeek('order_date')
        else:  # month
            truncated_date = TruncMonth('order_date')
            
        # Aggregate by period
        sales_by_period = orders.annotate(
            period=truncated_date
        ).values('period').annotate(
            order_count=Count('id'),
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount')
        ).order_by('period')
        
        return list(sales_by_period)
    
    @staticmethod
    def get_top_products(limit=10, start_date=None, end_date=None):
        """
        Get top selling products.
        """
        # Default to last 30 days if no date range specified
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
            
        if not end_date:
            end_date = timezone.now()
            
        # Get all order items from orders in the period
        order_items = OrderItem.objects.filter(
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
            order__status__in=['completed', 'delivered']
        )
        
        # Aggregate by product
        top_products = order_items.values(
            'product__id', 'product__name', 'product__code'
        ).annotate(
            quantity_sold=Sum('quantity'),
            total_revenue=Sum(
                ExpressionWrapper(
                    F('unit_price') * F('quantity') - F('discount_amount'),
                    output_field=DecimalField()
                )
            )
        ).order_by('-quantity_sold')[:limit]
        
        return list(top_products)
    
    @staticmethod
    def get_top_categories(limit=10, start_date=None, end_date=None):
        """
        Get top selling categories.
        """
        # Default to last 30 days if no date range specified
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
            
        if not end_date:
            end_date = timezone.now()
            
        # Get all order items from orders in the period
        order_items = OrderItem.objects.filter(
            order__order_date__gte=start_date,
            order__order_date__lte=end_date,
            order__status__in=['completed', 'delivered'],
            product__category__isnull=False
        )
        
        # Aggregate by category
        top_categories = order_items.values(
            'product__category__id', 'product__category__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            total_revenue=Sum(
                ExpressionWrapper(
                    F('unit_price') * F('quantity') - F('discount_amount'),
                    output_field=DecimalField()
                )
            )
        ).order_by('-quantity_sold')[:limit]
        
        return list(top_categories)
    
    @staticmethod
    def get_top_customers(limit=10, start_date=None, end_date=None):
        """
        Get top customers by order value.
        """
        # Default to last 30 days if no date range specified
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
            
        if not end_date:
            end_date = timezone.now()
            
        # Get all orders in the period
        orders = Order.objects.filter(
            order_date__gte=start_date,
            order_date__lte=end_date,
            status__in=['completed', 'delivered']
        )
        
        # Aggregate by customer
        top_customers = orders.values(
            'customer__id', 'customer__name', 'customer__company_name'
        ).annotate(
            order_count=Count('id'),
            total_spent=Sum('total_amount')
        ).order_by('-total_spent')[:limit]
        
        return list(top_customers)
    
    @staticmethod
    def get_inventory_status(category=None, low_stock_threshold=10):
        """
        Get inventory status report.
        """
        # Base query
        products = Product.objects.filter(is_active=True, is_physical=True)
        
        # Filter by category if specified
        if category:
            products = products.filter(category=category)
            
        # Annotate with stock status
        inventory_status = products.annotate(
            low_stock=ExpressionWrapper(
                Q(stock__lte=low_stock_threshold),
                output_field=models.BooleanField()
            ),
            out_of_stock=ExpressionWrapper(
                Q(stock=0),
                output_field=models.BooleanField()
            )
        ).values(
            'id', 'name', 'code', 'stock', 'low_stock', 'out_of_stock', 
            'category__name'
        ).order_by('stock')
        
        # Summary statistics
        summary = {
            'total_products': products.count(),
            'low_stock_count': products.filter(stock__lte=low_stock_threshold).count(),
            'out_of_stock_count': products.filter(stock=0).count(),
            'total_stock_value': sum(p.stock * p.price for p in products),
        }
        
        return {
            'summary': summary,
            'products': list(inventory_status)
        }
    
    @staticmethod
    def get_payment_statistics(start_date=None, end_date=None):
        """
        Get payment method statistics.
        """
        # Default to last 30 days if no date range specified
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
            
        if not end_date:
            end_date = timezone.now()
            
        # Get all payments in the period
        payments = Payment.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date,
            is_successful=True
        )
        
        # Aggregate by payment method
        payment_stats = payments.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')
        
        # Calculate percentages
        total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
        
        for stat in payment_stats:
            stat['percentage'] = (stat['total_amount'] / total_amount * 100) if total_amount > 0 else 0
            
        return list(payment_stats)
    
    @staticmethod
    def get_customer_acquisition(period='month', start_date=None, end_date=None):
        """
        Get customer acquisition data grouped by time period.
        """
        # Default to last 12 months if no date range specified
        if not start_date:
            if period == 'day':
                start_date = timezone.now() - timedelta(days=30)
            elif period == 'week':
                start_date = timezone.now() - timedelta(weeks=12)
            else:  # month
                start_date = timezone.now() - timedelta(days=365)
                
        if not end_date:
            end_date = timezone.now()
            
        # Base query for customers created in the period
        customers = Customer.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Group by period
        if period == 'day':
            truncated_date = TruncDay('created_at')
        elif period == 'week':
            truncated_date = TruncWeek('created_at')
        else:  # month
            truncated_date = TruncMonth('created_at')
            
        # Aggregate by period
        acquisition_by_period = customers.annotate(
            period=truncated_date
        ).values('period').annotate(
            new_customers=Count('id')
        ).order_by('period')
        
        return list(acquisition_by_period)