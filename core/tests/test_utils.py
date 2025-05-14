from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
import string

from customers.models import Customer, Address, Contact
from products.models import Category, Product
from orders.models import Order, OrderItem

User = get_user_model()


class TestDataGenerator:
    """
    Utility class for generating test data.
    
    This can be used across different test cases to create common test objects
    without duplicating setup code.
    """
    
    @staticmethod
    def create_user(username=None, is_staff=False):
        """Create a test user."""
        if username is None:
            username = ''.join(random.choices(string.ascii_lowercase, k=8))
            
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=f"{username}pass",
            is_staff=is_staff
        )
    
    @staticmethod
    def create_customer(user=None, customer_type='individual', name=None):
        """Create a test customer."""
        if user is None:
            user = TestDataGenerator.create_user()
            
        if name is None:
            name = f"Customer {random.randint(1000, 9999)}"
        
        customer_data = {
            'name': name,
            'type': customer_type,
            'email': f"{name.lower().replace(' ', '')}@example.com",
            'phone': f"555{random.randint(1000000, 9999999)}",
            'owner': user
        }
        
        if customer_type == 'corporate':
            customer_data['company_name'] = f"{name} Corporation"
            customer_data['tax_office'] = "Test Tax Office"
            customer_data['tax_number'] = str(random.randint(1000000000, 9999999999))
        
        return Customer.objects.create(**customer_data)
    
    @staticmethod
    def create_address(customer, address_type='shipping', is_default=False):
        """Create a test address for a customer."""
        return Address.objects.create(
            customer=customer,
            title=f"{address_type.capitalize()} Address",
            type=address_type,
            address_line1=f"{random.randint(1, 999)} Test Street",
            address_line2=f"Apt {random.randint(1, 100)}",
            city="Test City",
            state="Test State",
            postal_code=f"{random.randint(10000, 99999)}",
            country="Türkiye",
            is_default=is_default
        )
    
    @staticmethod
    def create_contact(customer, is_primary=False):
        """Create a test contact for a customer."""
        first_name = random.choice(["Ali", "Mehmet", "Ayşe", "Fatma", "Ahmet"])
        last_name = random.choice(["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin"])
        
        return Contact.objects.create(
            customer=customer,
            name=f"{first_name} {last_name}",
            title=random.choice(["CEO", "CTO", "CFO", "Manager", "Director"]),
            department=random.choice(["Management", "IT", "Finance", "Sales", "Marketing"]),
            email=f"{first_name.lower()}.{last_name.lower()}@{customer.name.lower().replace(' ', '')}.com",
            phone=f"555{random.randint(1000000, 9999999)}",
            is_primary=is_primary
        )
    
    @staticmethod
    def create_category(name=None, parent=None):
        """Create a test product category."""
        if name is None:
            name = f"Category {random.randint(100, 999)}"
        
        return Category.objects.create(
            name=name,
            description=f"Description for {name}",
            parent=parent
        )
    
    @staticmethod
    def create_product(category=None, price=None, stock=None):
        """Create a test product."""
        if category is None:
            category = TestDataGenerator.create_category()
            
        if price is None:
            price = Decimal(f"{random.randint(50, 1000)}.{random.randint(0, 99):02d}")
            
        if stock is None:
            stock = random.randint(0, 100)
        
        product_name = f"Product {random.randint(1000, 9999)}"
        
        return Product.objects.create(
            code=f"P{random.randint(10000, 99999)}",
            name=product_name,
            description=f"Description for {product_name}",
            category=category,
            price=price,
            cost=price * Decimal('0.6'),  # 60% of price
            tax_rate=random.choice([1, 8, 18]),
            stock=stock,
            status='available'
        )
    
    @staticmethod
    def create_order(customer=None, user=None, status='draft'):
        """Create a test order."""
        if customer is None:
            if user is None:
                user = TestDataGenerator.create_user()
            customer = TestDataGenerator.create_customer(user=user)
        
        # Create addresses if they don't exist
        if customer.addresses.filter(type='billing').count() == 0:
            billing_address = TestDataGenerator.create_address(customer, 'billing', True)
        else:
            billing_address = customer.addresses.filter(type='billing').first()
            
        if customer.addresses.filter(type='shipping').count() == 0:
            shipping_address = TestDataGenerator.create_address(customer, 'shipping', True)
        else:
            shipping_address = customer.addresses.filter(type='shipping').first()
        
        return Order.objects.create(
            order_number=f"ORD-{random.randint(10000, 99999)}",
            customer=customer,
            status=status,
            billing_address=billing_address,
            shipping_address=shipping_address,
            payment_method=random.choice(['credit_card', 'bank_transfer', 'cash']),
            shipping_cost=Decimal(f"{random.randint(0, 50)}.{random.randint(0, 99):02d}"),
            owner=customer.owner
        )
    
    @staticmethod
    def add_order_items(order, num_items=2):
        """Add random items to an order."""
        items = []
        
        for _ in range(num_items):
            product = TestDataGenerator.create_product()
            quantity = random.randint(1, 5)
            
            item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                tax_rate=product.tax_rate
            )
            
            items.append(item)
        
        # Calculate order totals
        order.calculate_totals()
        
        return items


class TestUtilsTest(TestCase):
    """Test the test utilities themselves."""
    
    def test_create_user(self):
        """Test creating a user."""
        user = TestDataGenerator.create_user('testuser')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertFalse(user.is_staff)
        
        staff_user = TestDataGenerator.create_user('staffuser', is_staff=True)
        self.assertTrue(staff_user.is_staff)
    
    def test_create_customer(self):
        """Test creating a customer."""
        user = TestDataGenerator.create_user()
        
        individual = TestDataGenerator.create_customer(user, 'individual', 'Individual Test')
        self.assertEqual(individual.type, 'individual')
        self.assertEqual(individual.name, 'Individual Test')
        self.assertEqual(individual.owner, user)
        
        corporate = TestDataGenerator.create_customer(user, 'corporate', 'Corporate Test')
        self.assertEqual(corporate.type, 'corporate')
        self.assertIsNotNone(corporate.company_name)
        self.assertIsNotNone(corporate.tax_number)
    
    def test_create_order_with_items(self):
        """Test creating an order with items."""
        # Create an order with random items
        order = TestDataGenerator.create_order()
        items = TestDataGenerator.add_order_items(order, 3)
        
        # Verify order
        self.assertEqual(order.items.count(), 3)
        self.assertGreater(order.total_amount, 0)
        
        # Verify items
        for item in items:
            self.assertEqual(item.order, order)