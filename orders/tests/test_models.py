from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from orders.models import Order, OrderItem, Payment, Shipment
from customers.models import Customer, Address
from products.models import Product, Category

User = get_user_model()


class OrderModelTest(TestCase):
    """Test cases for the Order model."""
    
    def setUp(self):
        """Set up test data for Order model tests."""
        # Create a user for order ownership
        self.user = User.objects.create_user(
            username='orderuser',
            email='orders@example.com',
            password='orderpassword'
        )
        
        # Create a customer for order relationship
        self.customer = Customer.objects.create(
            name='Test Customer',
            type='individual',
            email='customer@example.com',
            phone='5551234567',
            owner=self.user
        )
        
        # Create a billing address
        self.billing_address = Address.objects.create(
            customer=self.customer,
            title='Fatura Adresi',
            type='billing',
            address_line1='Fatura Caddesi No:1',
            city='İstanbul',
            postal_code='34100',
            is_default=True
        )
        
        # Create a shipping address
        self.shipping_address = Address.objects.create(
            customer=self.customer,
            title='Teslimat Adresi',
            type='shipping',
            address_line1='Teslimat Sokak No:2',
            city='İstanbul',
            postal_code='34200',
            is_default=True
        )
        
        # Create a product category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create products for order items
        self.product1 = Product.objects.create(
            code='PROD001',
            name='Test Product 1',
            category=self.category,
            price=Decimal('100.00'),
            tax_rate=18,
            stock=50
        )
        
        self.product2 = Product.objects.create(
            code='PROD002',
            name='Test Product 2',
            category=self.category,
            price=Decimal('200.00'),
            tax_rate=8,
            stock=30
        )
        
        # Create an order
        self.order = Order.objects.create(
            order_number='ORD-001',
            customer=self.customer,
            status='pending',
            order_date=timezone.now(),
            billing_address=self.billing_address,
            shipping_address=self.shipping_address,
            payment_method='credit_card',
            payment_status='pending',
            shipping_cost=Decimal('15.00'),
            owner=self.user
        )
        
        # Create order items
        self.order_item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=2,
            unit_price=Decimal('100.00'),
            tax_rate=18
        )
        
        self.order_item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            quantity=1,
            unit_price=Decimal('200.00'),
            tax_rate=8,
            discount_amount=Decimal('20.00')
        )
        
        # Calculate order totals
        self.order.calculate_totals()
    
    def test_order_creation(self):
        """Test that orders can be created with valid data."""
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.order.order_number, 'ORD-001')
        self.assertEqual(self.order.customer, self.customer)
    
    def test_order_str_representation(self):
        """Test the string representation of orders."""
        expected_str = f"ORD-001 - {self.customer.name}"
        self.assertEqual(str(self.order), expected_str)
    
    def test_order_total_calculation(self):
        """Test order total calculation."""
        # Calculate expected values:
        # Item 1: 2 × 100 = 200, tax = 200 × 0.18 = 36
        # Item 2: 1 × 200 - 20 = 180, tax = 180 × 0.08 = 14.4
        # Subtotal = 200 + 180 = 380
        # Tax total = 36 + 14.4 = 50.4
        # Total with shipping = 380 + 50.4 + 15 = 445.4
        
        expected_subtotal = Decimal('380.00')
        expected_tax = Decimal('50.40')
        expected_total = Decimal('445.40')
        
        self.assertEqual(self.order.subtotal, expected_subtotal)
        self.assertEqual(self.order.tax_amount, expected_tax)
        self.assertEqual(self.order.total_amount, expected_total)
    
    def test_order_status_transitions(self):
        """Test order status transitions."""
        self.assertEqual(self.order.status, 'pending')
        
        # Change status to processing
        self.order.status = 'processing'
        self.order.save()
        self.assertEqual(self.order.status, 'processing')
        
        # Change status to shipped
        self.order.status = 'shipped'
        self.order.shipping_date = timezone.now()
        self.order.save()
        self.assertEqual(self.order.status, 'shipped')
        self.assertIsNotNone(self.order.shipping_date)
    
    def test_order_payment_status_transitions(self):
        """Test order payment status transitions."""
        self.assertEqual(self.order.payment_status, 'pending')
        
        # Change payment status to paid
        self.order.payment_status = 'paid'
        self.order.save()
        self.assertEqual(self.order.payment_status, 'paid')
    
    def test_order_get_absolute_url(self):
        """Test the get_absolute_url method."""
        expected_url = f"/orders/{self.order.pk}/"
        self.assertEqual(self.order.get_absolute_url(), expected_url)
    
    def test_order_customer_relationship(self):
        """Test the relationship between order and customer."""
        self.assertEqual(self.order.customer, self.customer)
        self.assertEqual(self.customer.orders.count(), 1)
        self.assertEqual(self.customer.orders.first(), self.order)
    
    def test_order_badge_classes(self):
        """Test the get_status_badge and get_payment_status_badge methods."""
        # Test status badge
        self.order.status = 'pending'
        self.assertEqual(self.order.get_status_badge(), 'badge-warning')
        
        self.order.status = 'delivered'
        self.assertEqual(self.order.get_status_badge(), 'badge-success')
        
        self.order.status = 'cancelled'
        self.assertEqual(self.order.get_status_badge(), 'badge-error')
        
        # Test payment status badge
        self.order.payment_status = 'pending'
        self.assertEqual(self.order.get_payment_status_badge(), 'badge-warning')
        
        self.order.payment_status = 'paid'
        self.assertEqual(self.order.get_payment_status_badge(), 'badge-success')
        
        self.order.payment_status = 'refunded'
        self.assertEqual(self.order.get_payment_status_badge(), 'badge-error')


class OrderItemModelTest(TestCase):
    """Test cases for the OrderItem model."""
    
    def setUp(self):
        """Set up test data for OrderItem model tests."""
        # Create minimal customer and product for testing
        self.customer = Customer.objects.create(
            name='Item Test Customer',
            type='individual'
        )
        
        self.product = Product.objects.create(
            code='ITEM001',
            name='Item Test Product',
            price=Decimal('150.00'),
            tax_rate=18,
            stock=100
        )
        
        # Create an order
        self.order = Order.objects.create(
            order_number='ITEM-ORD-001',
            customer=self.customer,
            status='pending'
        )
        
        # Create an order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            unit_price=Decimal('150.00'),
            tax_rate=18,
            discount_amount=Decimal('50.00')
        )
    
    def test_order_item_creation(self):
        """Test that order items can be created with valid data."""
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.order_item.quantity, 3)
    
    def test_order_item_str_representation(self):
        """Test the string representation of order items."""
        expected_str = f"{self.order.order_number} - {self.product.name} (3)"
        self.assertEqual(str(self.order_item), expected_str)
    
    def test_line_total_calculation(self):
        """Test line total calculation."""
        # (3 × 150) - 50 = 400
        expected_line_total = Decimal('400.00')
        self.assertEqual(self.order_item.line_total, expected_line_total)
    
    def test_tax_amount_calculation(self):
        """Test tax amount calculation."""
        # 400 × 0.18 = 72
        expected_tax = Decimal('72.00')
        self.assertEqual(self.order_item.tax_amount, expected_tax)
    
    def test_total_with_tax_calculation(self):
        """Test total with tax calculation."""
        # 400 + 72 = 472
        expected_total = Decimal('472.00')
        self.assertEqual(self.order_item.total_with_tax, expected_total)
    
    def test_order_relationship(self):
        """Test the relationship between order item and order."""
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order.items.first(), self.order_item)
    
    def test_product_relationship(self):
        """Test the relationship between order item and product."""
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.product.order_items.count(), 1)
        self.assertEqual(self.product.order_items.first(), self.order_item)


class PaymentModelTest(TestCase):
    """Test cases for the Payment model."""
    
    def setUp(self):
        """Set up test data for Payment model tests."""
        # Create minimal customer and order for testing
        self.customer = Customer.objects.create(
            name='Payment Test Customer',
            type='individual'
        )
        
        self.order = Order.objects.create(
            order_number='PAY-ORD-001',
            customer=self.customer,
            status='processing',
            total_amount=Decimal('500.00')
        )
        
        # Create a payment
        self.payment = Payment.objects.create(
            order=self.order,
            payment_method='credit_card',
            amount=Decimal('300.00'),
            payment_date=timezone.now(),
            transaction_id='TR-123456',
            notes='Partial payment',
            is_successful=True
        )
    
    def test_payment_creation(self):
        """Test that payments can be created with valid data."""
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(self.payment.payment_method, 'credit_card')
        self.assertEqual(self.payment.amount, Decimal('300.00'))
    
    def test_payment_str_representation(self):
        """Test the string representation of payments."""
        expected_str = f"{self.order.order_number} - Kredi Kartı - 300.00 ₺"
        self.assertEqual(str(self.payment), expected_str)
    
    def test_order_relationship(self):
        """Test the relationship between payment and order."""
        self.assertEqual(self.payment.order, self.order)
        self.assertEqual(self.order.payments.count(), 1)
        self.assertEqual(self.order.payments.first(), self.payment)


class ShipmentModelTest(TestCase):
    """Test cases for the Shipment model."""
    
    def setUp(self):
        """Set up test data for Shipment model tests."""
        # Create minimal customer and order for testing
        self.customer = Customer.objects.create(
            name='Shipment Test Customer',
            type='individual'
        )
        
        self.order = Order.objects.create(
            order_number='SHIP-ORD-001',
            customer=self.customer,
            status='processing'
        )
        
        # Create a shipment
        shipping_date = timezone.now()
        self.shipment = Shipment.objects.create(
            order=self.order,
            carrier='Test Kargo',
            tracking_number='TK123456789',
            shipping_date=shipping_date,
            estimated_delivery=shipping_date + timezone.timedelta(days=3),
            status='shipped',
            notes='Test shipment'
        )
    
    def test_shipment_creation(self):
        """Test that shipments can be created with valid data."""
        self.assertEqual(Shipment.objects.count(), 1)
        self.assertEqual(self.shipment.carrier, 'Test Kargo')
        self.assertEqual(self.shipment.tracking_number, 'TK123456789')
    
    def test_shipment_str_representation(self):
        """Test the string representation of shipments."""
        expected_str = f"{self.order.order_number} - Test Kargo - TK123456789"
        self.assertEqual(str(self.shipment), expected_str)
    
    def test_order_relationship(self):
        """Test the relationship between shipment and order."""
        self.assertEqual(self.shipment.order, self.order)
        self.assertEqual(self.order.shipments.count(), 1)
        self.assertEqual(self.order.shipments.first(), self.shipment)
    
    def test_shipment_status_badge(self):
        """Test the get_status_badge method."""
        self.shipment.status = 'preparing'
        self.assertEqual(self.shipment.get_status_badge(), 'badge-warning')
        
        self.shipment.status = 'shipped'
        self.assertEqual(self.shipment.get_status_badge(), 'badge-info')
        
        self.shipment.status = 'delivered'
        self.assertEqual(self.shipment.get_status_badge(), 'badge-success')
        
        self.shipment.status = 'failed'
        self.assertEqual(self.shipment.get_status_badge(), 'badge-error')