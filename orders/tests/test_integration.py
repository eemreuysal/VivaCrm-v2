from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from customers.models import Customer, Address
from products.models import Product, StockMovement
from orders.models import Order, OrderItem, Payment, Shipment

User = get_user_model()


class OrderProcessIntegrationTest(TestCase):
    """Integration tests for the order processing flow."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Create customer with addresses
        self.customer = Customer.objects.create(
            name='Integration Test Customer',
            type='individual',
            email='integration@example.com',
            phone='5551234567',
            owner=self.user
        )
        
        self.billing_address = Address.objects.create(
            customer=self.customer,
            title='Billing Address',
            type='billing',
            address_line1='Billing Street 123',
            city='Istanbul',
            postal_code='34100',
            is_default=True
        )
        
        self.shipping_address = Address.objects.create(
            customer=self.customer,
            title='Shipping Address',
            type='shipping',
            address_line1='Shipping Avenue 456',
            city='Istanbul',
            postal_code='34200',
            is_default=True
        )
        
        # Create products with stock
        self.product1 = Product.objects.create(
            code='INT001',
            name='Integration Product 1',
            price=Decimal('100.00'),
            cost=Decimal('60.00'),
            tax_rate=18,
            stock=50
        )
        
        self.product2 = Product.objects.create(
            code='INT002',
            name='Integration Product 2',
            price=Decimal('200.00'),
            cost=Decimal('120.00'),
            tax_rate=18,
            stock=30
        )
    
    def test_full_order_process(self):
        """Test the complete order process from creation to delivery."""
        # Step 1: Create an order
        order = Order.objects.create(
            order_number='INT-ORD-001',
            customer=self.customer,
            status='draft',
            billing_address=self.billing_address,
            shipping_address=self.shipping_address,
            payment_method='credit_card',
            shipping_cost=Decimal('15.00'),
            owner=self.user
        )
        
        # Verify order creation
        self.assertEqual(order.status, 'draft')
        self.assertEqual(order.payment_status, 'pending')
        
        # Step 2: Add items to the order
        order_item1 = OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=2,
            unit_price=self.product1.price,
            tax_rate=self.product1.tax_rate
        )
        
        order_item2 = OrderItem.objects.create(
            order=order,
            product=self.product2,
            quantity=1,
            unit_price=self.product2.price,
            tax_rate=self.product2.tax_rate
        )
        
        # Recalculate order totals
        order.calculate_totals()
        
        # Verify order item addition and total calculation
        self.assertEqual(order.items.count(), 2)
        expected_subtotal = (self.product1.price * 2) + self.product2.price
        expected_tax = (self.product1.price * 2 * Decimal('0.18')) + (self.product2.price * Decimal('0.18'))
        expected_total = expected_subtotal + expected_tax + Decimal('15.00')
        
        self.assertEqual(order.subtotal, expected_subtotal)
        self.assertEqual(order.tax_amount, expected_tax)
        self.assertEqual(order.total_amount, expected_total)
        
        # Step 3: Change order status to processing
        initial_product1_stock = self.product1.stock
        initial_product2_stock = self.product2.stock
        
        order.status = 'processing'
        order.save()
        
        # Verify status change
        self.assertEqual(order.status, 'processing')
        
        # Step 4: Make a payment
        payment = Payment.objects.create(
            order=order,
            payment_method='credit_card',
            amount=order.total_amount,
            transaction_id='TR-INT-001',
            is_successful=True
        )
        
        # Update payment status
        order.payment_status = 'paid'
        order.save()
        
        # Verify payment
        self.assertEqual(order.payments.count(), 1)
        self.assertEqual(order.payment_status, 'paid')
        
        # Step 5: Create shipment
        shipment = Shipment.objects.create(
            order=order,
            carrier='Integration Kargo',
            tracking_number='TRK-INT-001',
            status='shipped'
        )
        
        # Update order status to shipped
        order.status = 'shipped'
        order.shipping_date = timezone.now()
        order.save()
        
        # Verify shipment
        self.assertEqual(order.shipments.count(), 1)
        self.assertEqual(order.status, 'shipped')
        self.assertIsNotNone(order.shipping_date)
        
        # Step 6: Mark order as delivered
        shipment.status = 'delivered'
        shipment.actual_delivery = timezone.now()
        shipment.save()
        
        order.status = 'delivered'
        order.delivery_date = shipment.actual_delivery
        order.save()
        
        # Verify delivery
        self.assertEqual(shipment.status, 'delivered')
        self.assertEqual(order.status, 'delivered')
        self.assertIsNotNone(order.delivery_date)
        
        # Step 7: Complete the order and reduce stock
        order.status = 'completed'
        order.save()
        
        # Create stock movements for completed order
        StockMovement.objects.create(
            product=self.product1,
            movement_type='sale',
            quantity=-2,
            reference=f"Sipariş #{order.order_number}",
            notes=f"Satış - {order_item1.quantity} adet",
            created_by=self.user
        )
        
        StockMovement.objects.create(
            product=self.product2,
            movement_type='sale',
            quantity=-1,
            reference=f"Sipariş #{order.order_number}",
            notes=f"Satış - {order_item2.quantity} adet",
            created_by=self.user
        )
        
        # Refresh products from DB
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        
        # Verify stock reduction
        self.assertEqual(self.product1.stock, initial_product1_stock - 2)
        self.assertEqual(self.product2.stock, initial_product2_stock - 1)
        
        # Verify final order status
        self.assertEqual(order.status, 'completed')
    
    def test_order_with_partial_payment(self):
        """Test an order with partial payment."""
        # Create an order
        order = Order.objects.create(
            order_number='INT-PART-001',
            customer=self.customer,
            status='processing',
            billing_address=self.billing_address,
            shipping_address=self.shipping_address,
            payment_method='bank_transfer',
            owner=self.user
        )
        
        # Add items to the order
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=3,
            unit_price=self.product1.price,
            tax_rate=self.product1.tax_rate
        )
        
        # Calculate order totals
        order.calculate_totals()
        
        # Make a partial payment
        payment = Payment.objects.create(
            order=order,
            payment_method='bank_transfer',
            amount=order.total_amount / 2,  # Half of the total
            transaction_id='TR-PART-001',
            is_successful=True
        )
        
        # Check payment status (should be partially_paid)
        order.payment_status = 'partially_paid'
        order.save()
        
        # Verify partial payment
        self.assertEqual(order.payments.count(), 1)
        self.assertEqual(order.payment_status, 'partially_paid')
        
        # Make another payment for the remaining amount
        remaining_amount = order.total_amount - payment.amount
        
        second_payment = Payment.objects.create(
            order=order,
            payment_method='bank_transfer',
            amount=remaining_amount,
            transaction_id='TR-PART-002',
            is_successful=True
        )
        
        # Update payment status
        order.payment_status = 'paid'
        order.save()
        
        # Verify full payment
        self.assertEqual(order.payments.count(), 2)
        self.assertEqual(order.payment_status, 'paid')
        
        # Calculate total paid amount
        total_paid = order.payments.filter(is_successful=True).aggregate(
            total=models.Sum('amount'))['total']
            
        # Verify that the total paid matches the order total
        self.assertEqual(total_paid, order.total_amount)
    
    def test_order_cancellation(self):
        """Test order cancellation process."""
        # Create an order
        order = Order.objects.create(
            order_number='INT-CANCEL-001',
            customer=self.customer,
            status='pending',
            billing_address=self.billing_address,
            payment_method='cash',
            owner=self.user
        )
        
        # Add items to the order
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=1,
            unit_price=self.product1.price,
            tax_rate=self.product1.tax_rate
        )
        
        # Calculate order totals
        order.calculate_totals()
        
        # Make a payment
        Payment.objects.create(
            order=order,
            payment_method='cash',
            amount=order.total_amount,
            is_successful=True
        )
        
        # Update payment status
        order.payment_status = 'paid'
        order.save()
        
        # Now cancel the order
        order.status = 'cancelled'
        order.payment_status = 'cancelled'
        order.save()
        
        # Verify cancellation
        self.assertEqual(order.status, 'cancelled')
        self.assertEqual(order.payment_status, 'cancelled')
        
        # Refund the payment (create a negative payment)
        Payment.objects.create(
            order=order,
            payment_method='cash',
            amount=-order.total_amount,  # Negative amount for refund
            transaction_id='REFUND-001',
            notes='Order cancellation refund',
            is_successful=True
        )
        
        # Verify refund payment
        refund_total = order.payments.filter(amount__lt=0).aggregate(
            total=models.Sum('amount'))['total']
            
        self.assertEqual(abs(refund_total), order.total_amount)
        
        # Calculate net payment (should be zero after refund)
        net_payment = order.payments.filter(is_successful=True).aggregate(
            total=models.Sum('amount'))['total']
            
        self.assertEqual(net_payment, Decimal('0.00'))
    
    def test_order_shipping_partial(self):
        """Test partial shipping of an order."""
        # Create an order
        order = Order.objects.create(
            order_number='INT-PARTIAL-001',
            customer=self.customer,
            status='processing',
            billing_address=self.billing_address,
            shipping_address=self.shipping_address,
            payment_method='credit_card',
            owner=self.user
        )
        
        # Add multiple items to the order
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=2,
            unit_price=self.product1.price,
            tax_rate=self.product1.tax_rate
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product2,
            quantity=3,
            unit_price=self.product2.price,
            tax_rate=self.product2.tax_rate
        )
        
        # Calculate order totals
        order.calculate_totals()
        
        # Create first shipment (partial)
        first_shipment = Shipment.objects.create(
            order=order,
            carrier='First Cargo',
            tracking_number='PARTIAL-001',
            status='shipped',
            notes='First shipment with product1'
        )
        
        # Update order status
        order.status = 'partially_shipped'  # Custom status for this test
        order.shipping_date = first_shipment.shipping_date
        order.save()
        
        # Verify first shipment
        self.assertEqual(order.shipments.count(), 1)
        
        # Create second shipment
        second_shipment = Shipment.objects.create(
            order=order,
            carrier='Second Cargo',
            tracking_number='PARTIAL-002',
            status='shipped',
            notes='Second shipment with product2'
        )
        
        # Update order status to fully shipped
        order.status = 'shipped'
        order.save()
        
        # Verify second shipment
        self.assertEqual(order.shipments.count(), 2)
        
        # Mark both shipments as delivered
        first_shipment.status = 'delivered'
        first_shipment.actual_delivery = timezone.now()
        first_shipment.save()
        
        second_shipment.status = 'delivered'
        second_shipment.actual_delivery = timezone.now() + timezone.timedelta(days=1)  # Delivered a day later
        second_shipment.save()
        
        # Update order status to delivered only after all shipments are delivered
        if all(s.status == 'delivered' for s in order.shipments.all()):
            order.status = 'delivered'
            order.delivery_date = second_shipment.actual_delivery  # Use the latest delivery date
            order.save()
        
        # Verify final state
        self.assertEqual(order.status, 'delivered')
        self.assertEqual(order.shipments.count(), 2)
        self.assertEqual(
            order.delivery_date.date(), 
            second_shipment.actual_delivery.date()
        )