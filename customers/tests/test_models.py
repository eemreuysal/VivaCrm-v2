from django.test import TestCase
from django.contrib.auth import get_user_model
from customers.models import Customer, Address, Contact
from decimal import Decimal
from django.db.models import Sum

User = get_user_model()


class CustomerModelTest(TestCase):
    """Test cases for the Customer model."""
    
    def setUp(self):
        """Set up test data for Customer model tests."""
        # Create a user for ownership testing
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Create basic customers for testing
        self.individual_customer = Customer.objects.create(
            name='Ahmet Yılmaz',
            type='individual',
            email='ahmet@example.com',
            phone='5551234567',
            owner=self.user
        )
        
        self.corporate_customer = Customer.objects.create(
            name='Şirket Temsilcisi',
            type='corporate',
            company_name='ABC Ltd. Şti.',
            tax_office='Ankara VD',
            tax_number='1234567890',
            email='info@abc.com.tr',
            phone='5559876543',
            owner=self.user
        )
    
    def test_customer_creation(self):
        """Test that customers can be created with valid data."""
        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(self.individual_customer.name, 'Ahmet Yılmaz')
        self.assertEqual(self.corporate_customer.company_name, 'ABC Ltd. Şti.')
    
    def test_customer_str_representation(self):
        """Test the string representation of customers."""
        # Individual customer should use name
        self.assertEqual(str(self.individual_customer), 'Ahmet Yılmaz')
        
        # Corporate customer should use company name
        self.assertEqual(str(self.corporate_customer), 'ABC Ltd. Şti.')
    
    def test_customer_type_behavior(self):
        """Test differences between individual and corporate customers."""
        # Individual customers should not require company information
        self.assertEqual(self.individual_customer.type, 'individual')
        self.assertEqual(self.individual_customer.company_name, '')
        
        # Corporate customers should have company information
        self.assertEqual(self.corporate_customer.type, 'corporate')
        self.assertNotEqual(self.corporate_customer.company_name, '')
        self.assertNotEqual(self.corporate_customer.tax_number, '')
    
    def test_default_is_active_status(self):
        """Test that customers are active by default."""
        self.assertTrue(self.individual_customer.is_active)
        self.assertTrue(self.corporate_customer.is_active)
    
    def test_owner_relationship(self):
        """Test the relationship between customer and owner."""
        self.assertEqual(self.individual_customer.owner, self.user)
        self.assertEqual(self.corporate_customer.owner, self.user)
        
        # Test user's reverse relationship to owned customers
        self.assertEqual(self.user.owned_customers.count(), 2)
    
    def test_get_absolute_url(self):
        """Test the get_absolute_url method."""
        expected_url = f"/customers/{self.individual_customer.pk}/"
        self.assertEqual(
            self.individual_customer.get_absolute_url(),
            expected_url
        )
    
    def test_total_orders_property(self):
        """Test the total_orders property."""
        # Initially there should be no orders
        self.assertEqual(self.individual_customer.total_orders, 0)
        
        # We'll simulate orders by mocking the related manager
        # In a more comprehensive test, real Order objects would be created
        Customer.objects.filter(pk=self.individual_customer.pk).update(
            orders=None  # This is just a placeholder, as we're only testing the property
        )
        
        # Refresh the instance from the database
        self.individual_customer.refresh_from_db()
        
        # Test the property (will still be 0 without actual Order objects)
        self.assertEqual(self.individual_customer.total_orders, 0)
    
    def test_total_revenue_property(self):
        """Test the total_revenue property."""
        # Initially there should be no revenue
        self.assertEqual(self.individual_customer.total_revenue, 0)
        
        # Again, in a comprehensive test, real Order objects with amounts would be created
        # This just tests the property exists and returns expected default value


class AddressModelTest(TestCase):
    """Test cases for the Address model."""
    
    def setUp(self):
        """Set up test data for Address model tests."""
        # Create a customer for address relationship
        self.customer = Customer.objects.create(
            name='Mehmet Öz',
            type='individual',
            email='mehmet@example.com'
        )
        
        # Create addresses for testing
        self.billing_address = Address.objects.create(
            customer=self.customer,
            title='Ev Adresi',
            type='billing',
            address_line1='Park Caddesi No: 10',
            city='İstanbul',
            state='Beşiktaş',
            postal_code='34100',
            country='Türkiye',
            is_default=True
        )
        
        self.shipping_address = Address.objects.create(
            customer=self.customer,
            title='İş Adresi',
            type='shipping',
            address_line1='Bağdat Caddesi No: 45',
            city='İstanbul',
            state='Kadıköy',
            postal_code='34720',
            country='Türkiye',
            is_default=False
        )
    
    def test_address_creation(self):
        """Test that addresses can be created with valid data."""
        self.assertEqual(Address.objects.count(), 2)
        self.assertEqual(self.billing_address.title, 'Ev Adresi')
        self.assertEqual(self.shipping_address.city, 'İstanbul')
    
    def test_address_str_representation(self):
        """Test the string representation of addresses."""
        expected_str = f"Ev Adresi - {self.customer}"
        self.assertEqual(str(self.billing_address), expected_str)
    
    def test_address_type(self):
        """Test address types."""
        self.assertEqual(self.billing_address.type, 'billing')
        self.assertEqual(self.shipping_address.type, 'shipping')
    
    def test_default_address(self):
        """Test default address functionality."""
        self.assertTrue(self.billing_address.is_default)
        self.assertFalse(self.shipping_address.is_default)
    
    def test_customer_relationship(self):
        """Test the relationship between address and customer."""
        self.assertEqual(self.billing_address.customer, self.customer)
        self.assertEqual(self.shipping_address.customer, self.customer)
        
        # Test customer's reverse relationship to addresses
        self.assertEqual(self.customer.addresses.count(), 2)


class ContactModelTest(TestCase):
    """Test cases for the Contact model."""
    
    def setUp(self):
        """Set up test data for Contact model tests."""
        # Create a customer for contact relationship
        self.customer = Customer.objects.create(
            name='ABC Şirketi',
            type='corporate',
            company_name='ABC Ltd. Şti.',
            email='info@abc.com'
        )
        
        # Create contacts for testing
        self.primary_contact = Contact.objects.create(
            customer=self.customer,
            name='Ali Veli',
            title='Genel Müdür',
            department='Yönetim',
            email='ali@abc.com',
            phone='5551234567',
            is_primary=True
        )
        
        self.secondary_contact = Contact.objects.create(
            customer=self.customer,
            name='Ayşe Fatma',
            title='Satın Alma Müdürü',
            department='Satın Alma',
            email='ayse@abc.com',
            phone='5559876543',
            is_primary=False
        )
    
    def test_contact_creation(self):
        """Test that contacts can be created with valid data."""
        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(self.primary_contact.name, 'Ali Veli')
        self.assertEqual(self.secondary_contact.department, 'Satın Alma')
    
    def test_contact_str_representation(self):
        """Test the string representation of contacts."""
        expected_str = f"Ali Veli - {self.customer}"
        self.assertEqual(str(self.primary_contact), expected_str)
    
    def test_primary_contact(self):
        """Test primary contact functionality."""
        self.assertTrue(self.primary_contact.is_primary)
        self.assertFalse(self.secondary_contact.is_primary)
    
    def test_customer_relationship(self):
        """Test the relationship between contact and customer."""
        self.assertEqual(self.primary_contact.customer, self.customer)
        self.assertEqual(self.secondary_contact.customer, self.customer)
        
        # Test customer's reverse relationship to contacts
        self.assertEqual(self.customer.contacts.count(), 2)