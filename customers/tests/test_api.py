from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from customers.models import Customer, Address, Contact

User = get_user_model()


class CustomerAPITest(TestCase):
    """Test the Customer API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpassword'
        )
        
        # Create customers
        self.customer1 = Customer.objects.create(
            name='Test Customer 1',
            type='individual',
            email='customer1@example.com',
            phone='5551234567',
            owner=self.regular_user
        )
        
        self.customer2 = Customer.objects.create(
            name='Test Customer 2',
            type='corporate',
            company_name='Test Company',
            email='customer2@example.com',
            phone='5559876543',
            owner=self.other_user
        )
        
        # Set up API client
        self.client = APIClient()
        
        # API URL patterns
        self.list_url = reverse('api:customer-list')
        self.detail_url = reverse('api:customer-detail', args=[self.customer1.id])
        self.archive_url = reverse('api:customer-archive', args=[self.customer1.id])
        self.activate_url = reverse('api:customer-activate', args=[self.customer1.id])
    
    def test_list_customers_authenticated(self):
        """Test that authenticated users can list customers."""
        # Login as admin user
        self.client.force_authenticate(user=self.admin_user)
        
        # Test list endpoint
        response = self.client.get(self.list_url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Both customers
    
    def test_list_customers_filtered_by_owner(self):
        """Test that regular users can only see their own customers."""
        # Login as regular user
        self.client.force_authenticate(user=self.regular_user)
        
        # Test list endpoint
        response = self.client.get(self.list_url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only their customer
        self.assertEqual(response.data['results'][0]['id'], self.customer1.id)
    
    def test_retrieve_customer_detail(self):
        """Test retrieving a customer's details."""
        # Login as customer's owner
        self.client.force_authenticate(user=self.regular_user)
        
        # Test detail endpoint
        response = self.client.get(self.detail_url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Customer 1')
        self.assertEqual(response.data['email'], 'customer1@example.com')
    
    def test_create_customer(self):
        """Test creating a new customer."""
        # Login as regular user
        self.client.force_authenticate(user=self.regular_user)
        
        # Test data
        payload = {
            'name': 'New Customer',
            'type': 'individual',
            'email': 'new@example.com',
            'phone': '5557654321'
        }
        
        # Test create endpoint
        response = self.client.post(self.list_url, payload)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Customer')
        self.assertEqual(response.data['owner'], self.regular_user.id)
        
        # Check that customer was created in DB
        self.assertTrue(Customer.objects.filter(name='New Customer').exists())
    
    def test_update_customer(self):
        """Test updating a customer."""
        # Login as customer's owner
        self.client.force_authenticate(user=self.regular_user)
        
        # Test data
        payload = {
            'name': 'Updated Customer',
            'email': 'updated@example.com'
        }
        
        # Test update endpoint
        response = self.client.patch(self.detail_url, payload)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Customer')
        self.assertEqual(response.data['email'], 'updated@example.com')
        
        # Check that customer was updated in DB
        self.customer1.refresh_from_db()
        self.assertEqual(self.customer1.name, 'Updated Customer')
    
    def test_delete_customer(self):
        """Test deleting a customer."""
        # Login as customer's owner
        self.client.force_authenticate(user=self.regular_user)
        
        # Test delete endpoint
        response = self.client.delete(self.detail_url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that customer was deleted in DB
        self.assertFalse(Customer.objects.filter(id=self.customer1.id).exists())
    
    def test_owner_permissions(self):
        """Test that users can only modify their own customers."""
        # Login as other user
        self.client.force_authenticate(user=self.other_user)
        
        # Try to update customer1 (owned by regular_user)
        payload = {
            'name': 'Attempted Update',
        }
        response = self.client.patch(self.detail_url, payload)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Check that customer was not updated in DB
        self.customer1.refresh_from_db()
        self.assertEqual(self.customer1.name, 'Test Customer 1')
    
    def test_admin_permissions(self):
        """Test that admin users can modify any customer."""
        # Login as admin user
        self.client.force_authenticate(user=self.admin_user)
        
        # Update customer1
        payload = {
            'name': 'Admin Updated',
        }
        response = self.client.patch(self.detail_url, payload)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that customer was updated in DB
        self.customer1.refresh_from_db()
        self.assertEqual(self.customer1.name, 'Admin Updated')
    
    def test_archive_customer(self):
        """Test the archive action."""
        # Login as customer's owner
        self.client.force_authenticate(user=self.regular_user)
        
        # Test archive endpoint
        response = self.client.post(self.archive_url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'customer archived')
        
        # Check that customer was archived in DB
        self.customer1.refresh_from_db()
        self.assertFalse(self.customer1.is_active)
    
    def test_activate_customer(self):
        """Test the activate action."""
        # First, archive the customer
        self.customer1.is_active = False
        self.customer1.save()
        
        # Login as customer's owner
        self.client.force_authenticate(user=self.regular_user)
        
        # Test activate endpoint
        response = self.client.post(self.activate_url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'customer activated')
        
        # Check that customer was activated in DB
        self.customer1.refresh_from_db()
        self.assertTrue(self.customer1.is_active)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access API endpoints."""
        # Logout (no authentication)
        self.client.force_authenticate(user=None)
        
        # Try to list customers
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try to get customer details
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try to create a customer
        payload = {'name': 'Unauthorized Customer'}
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AddressAPITest(TestCase):
    """Test the Address API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            username='addressuser',
            email='address@example.com',
            password='addresspassword'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            name='Address Test Customer',
            type='individual',
            email='customer@example.com',
            owner=self.user
        )
        
        # Create addresses
        self.address = Address.objects.create(
            customer=self.customer,
            title='Test Address',
            type='billing',
            address_line1='Test Street 123',
            city='Test City',
            is_default=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # API URL patterns
        self.list_url = reverse('api:address-list')
        self.detail_url = reverse('api:address-detail', args=[self.address.id])
    
    def test_list_addresses(self):
        """Test listing addresses."""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_address(self):
        """Test creating a new address."""
        payload = {
            'customer': self.customer.id,
            'title': 'New Address',
            'type': 'shipping',
            'address_line1': 'New Street 456',
            'city': 'New City',
            'is_default': False
        }
        
        response = self.client.post(self.list_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 2)
        
        # Verify the new address
        new_address = Address.objects.get(title='New Address')
        self.assertEqual(new_address.customer, self.customer)
        self.assertEqual(new_address.type, 'shipping')
    
    def test_create_default_address(self):
        """Test creating a new default address changes other defaults."""
        # Create a new default address
        payload = {
            'customer': self.customer.id,
            'title': 'New Default Address',
            'type': 'billing',
            'address_line1': 'Default Street 789',
            'city': 'Default City',
            'is_default': True
        }
        
        response = self.client.post(self.list_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the original address is no longer default
        self.address.refresh_from_db()
        self.assertFalse(self.address.is_default)
        
        # Verify the new address is default
        new_address = Address.objects.get(title='New Default Address')
        self.assertTrue(new_address.is_default)


class ContactAPITest(TestCase):
    """Test the Contact API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            username='contactuser',
            email='contact@example.com',
            password='contactpassword'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            name='Contact Test Company',
            type='corporate',
            company_name='Test Corp',
            email='company@example.com',
            owner=self.user
        )
        
        # Create contact
        self.contact = Contact.objects.create(
            customer=self.customer,
            name='Test Contact',
            title='CEO',
            email='ceo@example.com',
            phone='5551234567',
            is_primary=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # API URL patterns
        self.list_url = reverse('api:contact-list')
        self.detail_url = reverse('api:contact-detail', args=[self.contact.id])
    
    def test_list_contacts(self):
        """Test listing contacts."""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_contact(self):
        """Test creating a new contact."""
        payload = {
            'customer': self.customer.id,
            'name': 'New Contact',
            'title': 'CTO',
            'email': 'cto@example.com',
            'phone': '5559876543',
            'is_primary': False
        }
        
        response = self.client.post(self.list_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 2)
        
        # Verify the new contact
        new_contact = Contact.objects.get(name='New Contact')
        self.assertEqual(new_contact.customer, self.customer)
        self.assertEqual(new_contact.title, 'CTO')
    
    def test_create_primary_contact(self):
        """Test creating a new primary contact changes other primaries."""
        # Create a new primary contact
        payload = {
            'customer': self.customer.id,
            'name': 'New Primary Contact',
            'title': 'COO',
            'email': 'coo@example.com',
            'is_primary': True
        }
        
        response = self.client.post(self.list_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the original contact is no longer primary
        self.contact.refresh_from_db()
        self.assertFalse(self.contact.is_primary)
        
        # Verify the new contact is primary
        new_contact = Contact.objects.get(name='New Primary Contact')
        self.assertTrue(new_contact.is_primary)