from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, ProductAttribute, ProductAttributeValue, StockMovement
from decimal import Decimal
from django.utils.text import slugify

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test cases for the Category model."""
    
    def setUp(self):
        """Set up test data for Category model tests."""
        # Create categories for testing
        self.parent_category = Category.objects.create(
            name='Elektronik',
            description='Elektronik ürünler'
        )
        
        self.child_category = Category.objects.create(
            name='Telefonlar',
            description='Akıllı telefonlar ve aksesuar',
            parent=self.parent_category
        )
    
    def test_category_creation(self):
        """Test that categories can be created with valid data."""
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(self.parent_category.name, 'Elektronik')
    
    def test_category_str_representation(self):
        """Test the string representation of categories."""
        self.assertEqual(str(self.parent_category), 'Elektronik')
        self.assertEqual(str(self.child_category), 'Elektronik > Telefonlar')
    
    def test_slug_generation(self):
        """Test automatic slug generation."""
        self.assertEqual(self.parent_category.slug, 'elektronik')
        self.assertEqual(self.child_category.slug, 'telefonlar')
    
    def test_parent_child_relationship(self):
        """Test parent-child relationship between categories."""
        self.assertEqual(self.child_category.parent, self.parent_category)
        self.assertEqual(self.parent_category.children.count(), 1)
        self.assertEqual(self.parent_category.children.first(), self.child_category)
    
    def test_default_is_active_status(self):
        """Test that categories are active by default."""
        self.assertTrue(self.parent_category.is_active)
        self.assertTrue(self.child_category.is_active)
    
    def test_get_absolute_url(self):
        """Test the get_absolute_url method."""
        expected_url = f"/products/category/{self.parent_category.slug}/"
        self.assertEqual(
            self.parent_category.get_absolute_url(),
            expected_url
        )


class ProductModelTest(TestCase):
    """Test cases for the Product model."""
    
    def setUp(self):
        """Set up test data for Product model tests."""
        # Create a category for product relationship
        self.category = Category.objects.create(
            name='Telefonlar',
            description='Akıllı telefonlar'
        )
        
        # Create products for testing
        self.product = Product.objects.create(
            code='IP14PRO',
            name='iPhone 14 Pro',
            description='Apple iPhone 14 Pro 128GB',
            category=self.category,
            price=Decimal('30000.00'),
            cost=Decimal('25000.00'),
            tax_rate=18,
            stock=50,
            status='available'
        )
        
        self.discounted_product = Product.objects.create(
            code='SAMS22',
            name='Samsung Galaxy S22',
            description='Samsung Galaxy S22 128GB',
            category=self.category,
            price=Decimal('20000.00'),
            cost=Decimal('15000.00'),
            discount_price=Decimal('18000.00'),
            tax_rate=18,
            stock=30,
            status='available'
        )
    
    def test_product_creation(self):
        """Test that products can be created with valid data."""
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(self.product.name, 'iPhone 14 Pro')
        self.assertEqual(self.product.price, Decimal('30000.00'))
    
    def test_product_str_representation(self):
        """Test the string representation of products."""
        self.assertEqual(str(self.product), 'IP14PRO - iPhone 14 Pro')
    
    def test_slug_generation(self):
        """Test automatic slug generation."""
        self.assertEqual(self.product.slug, 'iphone-14-pro')
    
    def test_category_relationship(self):
        """Test the relationship between product and category."""
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.category.products.count(), 2)
    
    def test_tax_amount_calculation(self):
        """Test tax amount calculation."""
        # Regular product
        expected_tax = self.product.price * Decimal('0.18')
        self.assertEqual(self.product.tax_amount, expected_tax)
        
        # Discounted product
        expected_tax = self.discounted_product.discount_price * Decimal('0.18')
        self.assertEqual(self.discounted_product.tax_amount, expected_tax)
    
    def test_price_with_tax_calculation(self):
        """Test price with tax calculation."""
        # Regular product
        expected_price = self.product.price * Decimal('1.18')
        self.assertEqual(self.product.price_with_tax, expected_price)
        
        # Discounted product
        expected_price = self.discounted_product.discount_price * Decimal('1.18')
        self.assertEqual(self.discounted_product.price_with_tax, expected_price)
    
    def test_profit_margin_calculation(self):
        """Test profit margin calculation."""
        # Regular product
        expected_margin = ((self.product.price - self.product.cost) / self.product.cost) * 100
        self.assertEqual(self.product.profit_margin, expected_margin)
        
        # Discounted product
        expected_margin = ((self.discounted_product.discount_price - self.discounted_product.cost) / 
                          self.discounted_product.cost) * 100
        self.assertEqual(self.discounted_product.profit_margin, expected_margin)
    
    def test_stock_management(self):
        """Test stock management (indirectly, as StockMovement updates stock)."""
        self.assertEqual(self.product.stock, 50)


class StockMovementModelTest(TestCase):
    """Test cases for the StockMovement model."""
    
    def setUp(self):
        """Set up test data for StockMovement model tests."""
        # Create a user for stock movement creation
        self.user = User.objects.create_user(
            username='stockmanager',
            email='stock@example.com',
            password='stockpassword'
        )
        
        # Create a product for stock movement
        self.product = Product.objects.create(
            code='TEST001',
            name='Test Product',
            price=Decimal('100.00'),
            cost=Decimal('80.00'),
            tax_rate=18,
            stock=10
        )
    
    def test_purchase_stock_movement(self):
        """Test stock movement for purchase type."""
        # Create a purchase movement
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='purchase',
            quantity=5,
            reference='PO-12345',
            notes='Initial stock purchase',
            created_by=self.user,
            unit_cost=Decimal('85.00')  # New unit cost
        )
        
        # Refresh product from DB
        self.product.refresh_from_db()
        
        # Test stock levels
        self.assertEqual(movement.previous_stock, 10)
        self.assertEqual(movement.new_stock, 15)
        self.assertEqual(self.product.stock, 15)
        
        # Test cost update - should be weighted average
        # (10 units * 80) + (5 units * 85) / 15 units
        expected_cost = ((10 * Decimal('80.00')) + (5 * Decimal('85.00'))) / 15
        self.assertAlmostEqual(self.product.cost, expected_cost)
    
    def test_sale_stock_movement(self):
        """Test stock movement for sale type."""
        # Create a sale movement
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='sale',
            quantity=-3,  # Negative for sales
            reference='SO-54321',
            notes='Sale to customer',
            created_by=self.user
        )
        
        # Refresh product from DB
        self.product.refresh_from_db()
        
        # Test stock levels
        self.assertEqual(movement.previous_stock, 10)
        self.assertEqual(movement.new_stock, 7)
        self.assertEqual(self.product.stock, 7)
        
        # Cost should remain unchanged
        self.assertEqual(self.product.cost, Decimal('80.00'))
    
    def test_adjustment_stock_movement(self):
        """Test stock movement for adjustment type."""
        # Create an adjustment movement to correct stock
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='adjustment',
            quantity=2,  # Positive for addition
            reference='ADJ-001',
            notes='Stock correction after inventory',
            created_by=self.user
        )
        
        # Refresh product from DB
        self.product.refresh_from_db()
        
        # Test stock levels
        self.assertEqual(movement.previous_stock, 10)
        self.assertEqual(movement.new_stock, 12)
        self.assertEqual(self.product.stock, 12)
    
    def test_negative_stock_prevention(self):
        """Test that stock can't go below zero."""
        # Try to create a sale movement for more than available stock
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='sale',
            quantity=-20,  # More than available (10)
            reference='SO-OVER',
            notes='Overselling test',
            created_by=self.user
        )
        
        # Refresh product from DB
        self.product.refresh_from_db()
        
        # Stock should be 0, not negative
        self.assertEqual(movement.new_stock, 0)
        self.assertEqual(self.product.stock, 0)
    
    def test_stock_movement_str_representation(self):
        """Test the string representation of stock movements."""
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='purchase',
            quantity=5,
            reference='PO-12345',
            created_by=self.user
        )
        
        expected_str = 'Test Product - Satın Alma - 5'
        self.assertEqual(str(movement), expected_str)