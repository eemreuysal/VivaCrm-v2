# VivaCRM v2.0 - Complete Development Documentation

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [Technical Architecture](#technical-architecture)
4. [Database Schema](#database-schema)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Architecture](#frontend-architecture)
7. [UI/UX Design System](#uiux-design-system)
8. [Page Specifications](#page-specifications)
9. [API Documentation](#api-documentation)
10. [Development Workflow](#development-workflow)
11. [Testing Strategy](#testing-strategy)
12. [Deployment Guide](#deployment-guide)
13. [Additional Development Guidelines](#additional-development-guidelines)

---

## 1. Executive Summary

VivaCRM v2.0 is a modern Customer Relationship Management system built with Django backend and HTMX + Alpine.js frontend. The system provides comprehensive customer management, order tracking, product catalog, and advanced reporting capabilities with a focus on Turkish market needs.

### Key Features
- Customer Management with full CRUD operations
- Product Catalog with inventory tracking
- Order Management with status workflows
- Advanced Dashboard with KPIs and visualizations
- Excel import/export functionality
- Multi-role user management
- Responsive design with Turkish UI

### Technical Highlights
- Server-side rendering with Django Templates
- Partial page updates using HTMX
- Client-side interactivity with Alpine.js
- Modern UI with TailwindCSS + DaisyUI
- PostgreSQL for data storage
- Redis for caching
- Celery for background tasks

---

## 2. Project Overview

### 2.1 Project Structure
```
vivacrm-v2/
├── core/                # Django settings and configurations
├── accounts/            # User authentication and management
├── customers/           # Customer management module
├── products/            # Product catalog module
├── orders/              # Order processing module
├── dashboard/           # Dashboard and analytics
├── reports/             # Reporting module
├── static/              # Static files (CSS, JS, images)
│   ├── css/            # TailwindCSS files
│   ├── js/             # JavaScript files
│   └── img/            # Images
├── templates/           # Django templates
│   ├── base/           # Base templates
│   ├── components/     # Reusable components
│   └── pages/          # Page templates
└── requirements/        # Python dependencies
```

### 2.2 Development Languages
- **Code & Comments**: English
- **UI Text**: Turkish
- **Currency**: USD ($)
- **Date Format**: DD.MM.YYYY
- **Time Zone**: UTC+3 (Istanbul)

### 2.3 Core Modules
1. **Authentication Module**: User management, roles, permissions
2. **Customer Module**: Customer CRUD, activities, relationships
3. **Product Module**: Product catalog, categories, inventory
4. **Order Module**: Order processing, status tracking, invoicing
5. **Dashboard Module**: KPIs, charts, real-time analytics
6. **Report Module**: Business reports, Excel exports
7. **Admin Module**: System configuration, user management

---

## 3. Technical Architecture

### 3.1 Backend Stack
```yaml
Core:
  - Django 5.0
  - Django REST Framework 3.14.0
  - Python 3.11+

Database:
  - PostgreSQL (primary database)
  - Redis (cache and session storage)

Authentication:
  - Django Built-in + Custom Login Form
  - Role-based permissions

Task Queue:
  - Celery
  - Redis (broker)

API Documentation:
  - drf-spectacular (OpenAPI 3.0)

Testing:
  - pytest-django
  - factory-boy

Development Tools:
  - django-debug-toolbar
  - django-extensions
  - black (code formatter)
  - pre-commit
```

### 3.2 Frontend Stack
```yaml
Template Engine:
  - Django Templates (server-side rendering)

Interactivity:
  - HTMX (partial page updates)
  - Alpine.js (client-side reactivity)

Styling:
  - TailwindCSS
  - DaisyUI components

Visualization:
  - ApexCharts (charts and graphs)
  - Leaflet + leaflet-choropleth (maps)

Tables:
  - DataTables.js

Forms:
  - django-crispy-forms
  - crispy-tailwind

File Processing:
  - pandas
  - openpyxl (Excel operations)
```

### 3.3 Architecture Principles
- **Server-Side First**: Leverage Django's template system
- **Progressive Enhancement**: Add interactivity with HTMX/Alpine.js
- **API-Driven**: RESTful APIs for external integrations
- **Cache-Heavy**: Redis caching for performance
- **Task Queue**: Asynchronous processing for heavy operations
- **Security First**: CSRF protection, input validation, secure sessions

---

## 4. Database Schema

### 4.1 User Model (Extended)
```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
```

### 4.2 Customer Model
```python
# customers/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Customer(models.Model):
    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('prospect', 'Prospect'),
        ('customer', 'Customer'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived')
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=100, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Location (for maps)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # CRM Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    source = models.CharField(max_length=50, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customers')
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_customers')
    
    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
```

### 4.3 Product Model
```python
# products/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_categories'
        verbose_name_plural = 'Product Categories'
    
    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued')
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Inventory
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Images
    featured_image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def discounted_price(self):
        if self.discount_percentage > 0:
            discount_amount = self.price * (self.discount_percentage / 100)
            return self.price - discount_amount
        return self.price
    
    @property
    def in_stock(self):
        return self.stock_quantity > 0
    
    @property
    def low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold
```

### 4.4 Order Model
```python
# orders/models.py
from django.db import models
from django.contrib.auth import get_user_model
from customers.models import Customer
from products.models import Product

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('other', 'Other')
    ]
    
    # Basic Information
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    
    # Shipping
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)
    
    # Billing
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional Information
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['order_date']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import datetime
            now = datetime.datetime.now()
            self.order_number = f"ORD-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_amount - self.discount_amount
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'order_items'
    
    @property
    def total_price(self):
        return (self.unit_price * self.quantity) - self.discount_amount
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
```

---

## 5. Backend Implementation

### 5.1 View Architecture (Django + HTMX)

```python
# customers/views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Customer
from .forms import CustomerForm

@login_required
def customer_list(request):
    """Customer list main page"""
    customers = Customer.objects.all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        customers = customers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(company_name__icontains=search)
        )
    
    # Filtering
    status = request.GET.get('status')
    if status:
        customers = customers.filter(status=status)
    
    # Pagination
    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    if request.headers.get('HX-Request'):
        # HTMX request - return only table part
        return render(request, 'customers/partials/customer_table.html', context)
    
    return render(request, 'customers/list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def customer_create(request):
    """Create new customer (modal)"""
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            
            # HTMX trigger to refresh table
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'customerListChanged'
            return response
    else:
        form = CustomerForm()
    
    return render(request, 'customers/partials/customer_form.html', {
        'form': form,
        'action': 'create'
    })


@login_required
@require_http_methods(["GET", "POST"])
def customer_edit(request, pk):
    """Edit customer (modal)"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            
            # HTMX trigger to refresh table
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'customerListChanged'
            return response
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customers/partials/customer_form.html', {
        'form': form,
        'customer': customer,
        'action': 'edit'
    })


@login_required
@require_http_methods(["DELETE"])
def customer_delete(request, pk):
    """Delete customer"""
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    
    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'customerListChanged'
    return response


@login_required
def customer_detail(request, pk):
    """Customer detail page"""
    customer = get_object_or_404(Customer, pk=pk)
    orders = customer.orders.all()[:10]
    
    context = {
        'customer': customer,
        'orders': orders,
    }
    
    return render(request, 'customers/detail.html', context)
```

### 5.2 Form Implementation

```python
# customers/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column, Submit
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'company_name', 'title', 'status', 'assigned_to',
            'address', 'city', 'state', 'postal_code', 'country',
            'notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='w-full md:w-1/2'),
                Column('last_name', css_class='w-full md:w-1/2'),
                css_class='flex flex-wrap -mx-3'
            ),
            Row(
                Column('email', css_class='w-full md:w-1/2'),
                Column('phone', css_class='w-full md:w-1/2'),
                css_class='flex flex-wrap -mx-3'
            ),
            Row(
                Column('company_name', css_class='w-full md:w-1/2'),
                Column('title', css_class='w-full md:w-1/2'),
                css_class='flex flex-wrap -mx-3'
            ),
            Row(
                Column('status', css_class='w-full md:w-1/2'),
                Column('assigned_to', css_class='w-full md:w-1/2'),
                css_class='flex flex-wrap -mx-3'
            ),
            'address',
            Row(
                Column('city', css_class='w-full md:w-1/3'),
                Column('state', css_class='w-full md:w-1/3'),
                Column('postal_code', css_class='w-full md:w-1/3'),
                css_class='flex flex-wrap -mx-3'
            ),
            'country',
            'notes',
            Submit('submit', 'Kaydet', css_class='btn btn-primary')
        )
```

### 5.3 API Implementation (DRF)

```python
# api/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum

from customers.models import Customer
from .serializers import CustomerSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'assigned_to', 'city', 'country']
    search_fields = ['first_name', 'last_name', 'email', 'company_name']
    ordering_fields = ['created_at', 'updated_at', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            total_orders=Count('orders'),
            total_revenue=Sum('orders__total_amount')
        )
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Customer statistics"""
        stats = {
            'total_customers': Customer.objects.count(),
            'active_customers': Customer.objects.filter(status='customer').count(),
            'leads': Customer.objects.filter(status='lead').count(),
            'by_status': Customer.objects.values('status').annotate(count=Count('id')),
            'by_country': Customer.objects.values('country').annotate(count=Count('id')).order_by('-count')[:10]
        }
        return Response(stats)
```

### 5.4 Excel Operations

```python
# excel_operations/views.py
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from products.models import Product, ProductCategory
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

@login_required
def product_excel_template(request):
    """Generate Excel template for product import"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Ürünler"
    
    # Headers
    headers = [
        'SKU*', 'ÜRÜN İSMİ*', 'BARKOD', 'FİYAT*', 'ÜRÜN MALİYETİ',
        'KATEGORİ', 'STOK MİKTARI', 'GÖRSEL URL'
    ]
    
    # Header row styling
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Example data
    ws.append(['PRD001', 'Örnek Ürün', '123456789', '99.90', '45.00', 'Elektronik', '100', 'https://example.com/image.jpg'])
    
    # Column widths
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 30
    
    # Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=urun_sablonu.xlsx'
    wb.save(response)
    return response

@login_required
@require_http_methods(["GET", "POST"])
def product_excel_upload(request):
    """Upload and process product Excel file"""
    if request.method == "POST":
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Dosya bulunamadı'}, status=400)
        
        file = request.FILES['file']
        
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Check required columns
            required_columns = ['SKU', 'ÜRÜN İSMİ', 'FİYAT']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return JsonResponse({
                    'error': f'Eksik sütunlar: {", ".join(missing_columns)}'
                }, status=400)
            
            # Process data
            success_count = 0
            error_count = 0
            errors = []
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Create or find category
                        category = None
                        if pd.notna(row.get('KATEGORİ')):
                            category, _ = ProductCategory.objects.get_or_create(
                                name=row['KATEGORİ']
                            )
                        
                        # Create or update product
                        product_data = {
                            'name': row['ÜRÜN İSMİ'],
                            'price': float(row['FİYAT']),
                            'barcode': row.get('BARKOD', ''),
                            'cost': float(row.get('ÜRÜN MALİYETİ', 0)),
                            'category': category,
                            'stock_quantity': int(row.get('STOK MİKTARI', 0)),
                            'image_url': row.get('GÖRSEL URL', ''),
                        }
                        
                        product, created = Product.objects.update_or_create(
                            sku=row['SKU'],
                            defaults=product_data
                        )
                        
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Satır {index + 2}: {str(e)}")
                        if error_count > 10:  # Stop after 10 errors
                            break
            
            return JsonResponse({
                'success': True,
                'message': f'{success_count} ürün başarıyla işlendi.',
                'errors': errors[:10]  # Show first 10 errors
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Dosya işlenirken hata: {str(e)}'
            }, status=400)
    
    return render(request, 'excel_operations/product_upload.html')
```

---

## 6. Frontend Architecture

### 6.1 Django Settings

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'corsheaders',
    'crispy_forms',
    'crispy_tailwind',
    'debug_toolbar',
    'rest_framework',
    'django_filters',
    'leaflet',
    'django_celery_beat',
    'django_celery_results',
    
    # Apps
    'accounts',
    'customers',
    'products',
    'orders',
    'dashboard',
    'reports',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 6.2 Base Template Structure

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="tr" data-theme="vivacrm">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}VivaCRM{% endblock %}</title>
    
    <!-- TailwindCSS & DaisyUI -->
    <link href="{% static 'css/tailwind.css' %}" rel="stylesheet">
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    
    <!-- ApexCharts -->
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    
    <!-- Leaflet -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/dataTables.bootstrap5.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
    
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-base-200">
    <!-- Navbar -->
    <div class="navbar bg-base-100 shadow-lg">
        <div class="navbar-start">
            <div class="dropdown">
                <label tabindex="0" class="btn btn-ghost lg:hidden">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16" />
                    </svg>
                </label>
                <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
                    <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
                    <li><a href="{% url 'customer_list' %}">Müşteriler</a></li>
                    <li><a href="{% url 'product_list' %}">Ürünler</a></li>
                    <li><a href="{% url 'order_list' %}">Siparişler</a></li>
                    <li><a href="{% url 'report_list' %}">Raporlar</a></li>
                </ul>
            </div>
            <a class="btn btn-ghost normal-case text-xl" href="{% url 'dashboard' %}">VivaCRM</a>
        </div>
        
        <div class="navbar-center hidden lg:flex">
            <ul class="menu menu-horizontal px-1">
                <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
                <li><a href="{% url 'customer_list' %}">Müşteriler</a></li>
                <li><a href="{% url 'product_list' %}">Ürünler</a></li>
                <li><a href="{% url 'order_list' %}">Siparişler</a></li>
                <li><a href="{% url 'report_list' %}">Raporlar</a></li>
            </ul>
        </div>
        
        <div class="navbar-end">
            <div class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-ghost btn-circle avatar">
                    <div class="w-10 rounded-full">
                        <img src="{% if user.avatar %}{{ user.avatar.url }}{% else %}/static/img/avatar-default.png{% endif %}" />
                    </div>
                </label>
                <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
                    <li><a href="{% url 'profile' %}">Profil</a></li>
                    <li><a href="{% url 'settings' %}">Ayarlar</a></li>
                    <li><a href="{% url 'logout' %}">Çıkış</a></li>
                </ul>
            </div>
        </div>
    </div>
    
    <!-- Main Content -->
    <main class="container mx-auto px-4 py-8">
        {% if messages %}
            <div class="toast toast-top toast-end">
                {% for message in messages %}
                    <div class="alert alert-{{ message.tags }} shadow-lg">
                        <span>{{ message }}</span>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
        
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="footer p-10 bg-base-200 text-base-content">
        <aside>
            <p>VivaCRM © 2024 - Tüm hakları saklıdır.</p>
        </aside>
    </footer>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 6.3 HTMX and Alpine.js Integration

```html
<!-- templates/customers/list.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Müşteriler - VivaCRM{% endblock %}

{% block content %}
<div class="container mx-auto">
    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Müşteriler</h1>
        <button 
            class="btn btn-primary"
            hx-get="{% url 'customer_create' %}"
            hx-target="#modal-container"
            hx-trigger="click">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Yeni Müşteri
        </button>
    </div>
    
    <!-- Filters -->
    <div class="card bg-base-100 shadow-xl mb-6">
        <div class="card-body">
            <form hx-get="{% url 'customer_list' %}" 
                  hx-target="#customer-table-container"
                  hx-trigger="submit, change delay:500ms from:input"
                  class="grid grid-cols-1 md:grid-cols-4 gap-4">
                
                <div class="form-control">
                    <input type="text" 
                           name="search" 
                           placeholder="Ara..." 
                           value="{{ search }}"
                           class="input input-bordered" />
                </div>
                
                <div class="form-control">
                    <select name="status" class="select select-bordered">
                        <option value="">Tüm Durumlar</option>
                        <option value="lead" {% if status == 'lead' %}selected{% endif %}>Lead</option>
                        <option value="prospect" {% if status == 'prospect' %}selected{% endif %}>Prospect</option>
                        <option value="customer" {% if status == 'customer' %}selected{% endif %}>Customer</option>
                        <option value="inactive" {% if status == 'inactive' %}selected{% endif %}>Inactive</option>
                    </select>
                </div>
                
                <div class="form-control">
                    <button type="submit" class="btn btn-outline">Filtrele</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Customer Table -->
    <div id="customer-table-container">
        {% include 'customers/partials/customer_table.html' %}
    </div>
</div>

<!-- Modal Container -->
<div id="modal-container"></div>

<script>
    // HTMX event listeners
    document.body.addEventListener('customerListChanged', function() {
        htmx.trigger('#customer-table-container', 'htmx:afterSettle');
    });
</script>
{% endblock %}
```

---

## 7. UI/UX Design System

### 7.1 Color Palette

```css
/* static/css/viva-design-system.css */
:root {
  /* Primary Colors (Green Tones) */
  --viva-primary-50: #f0fdf4;   /* Very light green */
  --viva-primary-100: #dcfce7;  /* Light green */
  --viva-primary-200: #bbf7d0;  
  --viva-primary-300: #86efac;  
  --viva-primary-400: #4ade80;  
  --viva-primary-500: #22c55e;  /* Main green */
  --viva-primary-600: #16a34a;  
  --viva-primary-700: #15803d;  
  --viva-primary-800: #166534;  
  --viva-primary-900: #14532d;  /* Dark green */
  
  /* Secondary Colors (Blue Tones) */
  --viva-secondary-50: #eff6ff;   /* Very light blue */
  --viva-secondary-100: #dbeafe;  /* Light blue */
  --viva-secondary-200: #bfdbfe;  
  --viva-secondary-300: #93c5fd;  
  --viva-secondary-400: #60a5fa;  
  --viva-secondary-500: #3b82f6;  /* Main blue */
  --viva-secondary-600: #2563eb;  
  --viva-secondary-700: #1d4ed8;  
  --viva-secondary-800: #1e40af;  
  --viva-secondary-900: #1e3a8a;  /* Dark blue */
  
  /* Accent Colors (Amber/Orange Tones) */
  --viva-accent-50: #fffbeb;    /* Very light amber */
  --viva-accent-100: #fef3c7;   /* Light amber */
  --viva-accent-200: #fde68a;   
  --viva-accent-300: #fcd34d;   
  --viva-accent-400: #fbbf24;   
  --viva-accent-500: #f59e0b;   /* Main amber */
  --viva-accent-600: #d97706;   
  --viva-accent-700: #b45309;   
  --viva-accent-800: #92400e;   
  --viva-accent-900: #78350f;   /* Dark amber */
  
  /* Neutral Colors (Gray Tones) */
  --viva-gray-50: #f9fafb;    /* Very light gray */
  --viva-gray-100: #f3f4f6;   /* Light gray */
  --viva-gray-200: #e5e7eb;   
  --viva-gray-300: #d1d5db;   
  --viva-gray-400: #9ca3af;   
  --viva-gray-500: #6b7280;   /* Main gray */
  --viva-gray-600: #4b5563;   
  --viva-gray-700: #374151;   
  --viva-gray-800: #1f2937;   
  --viva-gray-900: #111827;   /* Dark gray */
  
  /* Semantic Colors */
  --viva-success: #22c55e;  /* Success - Green */
  --viva-warning: #f59e0b;  /* Warning - Amber */
  --viva-error: #ef4444;    /* Error - Red */
  --viva-info: #3b82f6;     /* Info - Blue */
  
  /* Typography */
  --viva-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --viva-font-mono: 'Fira Code', 'Courier New', monospace;
  
  /* Spacing */
  --viva-spacing-px: 1px;
  --viva-spacing-0: 0;
  --viva-spacing-0.5: 0.125rem;
  --viva-spacing-1: 0.25rem;
  --viva-spacing-1.5: 0.375rem;
  --viva-spacing-2: 0.5rem;
  --viva-spacing-2.5: 0.625rem;
  --viva-spacing-3: 0.75rem;
  --viva-spacing-3.5: 0.875rem;
  --viva-spacing-4: 1rem;
  --viva-spacing-5: 1.25rem;
  --viva-spacing-6: 1.5rem;
  --viva-spacing-7: 1.75rem;
  --viva-spacing-8: 2rem;
  --viva-spacing-9: 2.25rem;
  --viva-spacing-10: 2.5rem;
  --viva-spacing-12: 3rem;
  --viva-spacing-14: 3.5rem;
  --viva-spacing-16: 4rem;
  --viva-spacing-20: 5rem;
  --viva-spacing-24: 6rem;
  --viva-spacing-28: 7rem;
  --viva-spacing-32: 8rem;
  
  /* Border Radius */
  --viva-radius-none: 0;
  --viva-radius-sm: 0.125rem;
  --viva-radius-default: 0.25rem;
  --viva-radius-md: 0.375rem;
  --viva-radius-lg: 0.5rem;
  --viva-radius-xl: 0.75rem;
  --viva-radius-2xl: 1rem;
  --viva-radius-3xl: 1.5rem;
  --viva-radius-full: 9999px;
  
  /* Box Shadows */
  --viva-shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --viva-shadow-default: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --viva-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --viva-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --viva-shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  --viva-shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* DaisyUI Custom Theme */
[data-theme="vivacrm"] {
  --p: var(--viva-primary-500);
  --pf: var(--viva-primary-600);
  --pc: var(--viva-primary-50);
  
  --s: var(--viva-secondary-500);
  --sf: var(--viva-secondary-600);
  --sc: var(--viva-secondary-50);
  
  --a: var(--viva-accent-500);
  --af: var(--viva-accent-600);
  --ac: var(--viva-accent-50);
  
  --n: var(--viva-gray-800);
  --nf: var(--viva-gray-900);
  --nc: var(--viva-gray-50);
  
  --b1: var(--viva-gray-50);
  --b2: var(--viva-gray-100);
  --b3: var(--viva-gray-200);
  
  --bc: var(--viva-gray-800);
  
  --su: var(--viva-success);
  --wa: var(--viva-warning);
  --er: var(--viva-error);
  --in: var(--viva-info);
}
```

### 7.2 Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'viva-primary': {
          50: 'var(--viva-primary-50)',
          100: 'var(--viva-primary-100)',
          200: 'var(--viva-primary-200)',
          300: 'var(--viva-primary-300)',
          400: 'var(--viva-primary-400)',
          500: 'var(--viva-primary-500)',
          600: 'var(--viva-primary-600)',
          700: 'var(--viva-primary-700)',
          800: 'var(--viva-primary-800)',
          900: 'var(--viva-primary-900)',
        },
        'viva-secondary': {
          50: 'var(--viva-secondary-50)',
          100: 'var(--viva-secondary-100)',
          200: 'var(--viva-secondary-200)',
          300: 'var(--viva-secondary-300)',
          400: 'var(--viva-secondary-400)',
          500: 'var(--viva-secondary-500)',
          600: 'var(--viva-secondary-600)',
          700: 'var(--viva-secondary-700)',
          800: 'var(--viva-secondary-800)',
          900: 'var(--viva-secondary-900)',
        },
      },
    },
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        vivacrm: {
          "primary": "#22c55e",      // Green
          "secondary": "#3b82f6",    // Blue
          "accent": "#f59e0b",       // Amber
          "neutral": "#374151",      // Gray
          "base-100": "#f9fafb",     // Light gray background
          "info": "#3b82f6",         // Blue
          "success": "#22c55e",      // Green
          "warning": "#f59e0b",      // Amber
          "error": "#ef4444",        // Red
        },
      },
      "dark",
    ],
  },
}
```

---

## 8. Page Specifications

### 8.1 Login Page

```html
<!-- templates/accounts/login.html -->
{% extends 'base_auth.html' %}
{% load static %}

{% block title %}Giriş Yap - VivaCRM{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full">
        <div class="card bg-base-100 shadow-xl">
            <div class="card-body">
                <div class="text-center mb-8">
                    <img src="{% static 'img/logo.png' %}" alt="VivaCRM" class="h-12 mx-auto mb-4">
                    <h1 class="text-2xl font-bold">Giriş Yap</h1>
                    <p class="text-gray-600">CRM Sistemine</p>
                </div>
                
                <form method="post" action="{% url 'login' %}">
                    {% csrf_token %}
                    
                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text">Kullanıcı Adı</span>
                        </label>
                        <input type="text" 
                               name="username" 
                               placeholder="kullaniciadi" 
                               class="input input-bordered" 
                               required>
                    </div>
                    
                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text">Parola</span>
                        </label>
                        <input type="password" 
                               name="password" 
                               placeholder="••••••••" 
                               class="input input-bordered" 
                               required>
                    </div>
                    
                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text">Rol Seçimi</span>
                        </label>
                        <select name="role" class="select select-bordered">
                            <option value="admin">Admin</option>
                            <option value="standard">Standart</option>
                        </select>
                    </div>
                    
                    <div class="form-control mb-6">
                        <label class="label cursor-pointer">
                            <span class="label-text">Beni hatırla</span>
                            <input type="checkbox" name="remember" class="checkbox checkbox-primary">
                        </label>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-full">
                        GİRİŞ YAP
                    </button>
                    
                    <div class="text-center mt-4">
                        <a href="{% url 'password_reset' %}" class="link link-primary">
                            Şifremi unuttum
                        </a>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="text-center mt-6 text-sm text-gray-600">
            © 2025 VivaCRM | <a href="#" class="link">Koşullar</a> | <a href="#" class="link">Gizlilik</a>
        </div>
    </div>
</div>
{% endblock %}
```

### 8.2 Dashboard Page

```html
<!-- templates/dashboard/index.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Dashboard - VivaCRM{% endblock %}

{% block content %}
<div class="container mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Dashboard</h1>
        <div class="flex gap-2">
            <input type="date" 
                   id="start-date" 
                   class="input input-bordered input-sm"
                   value="{{ start_date }}">
            <span class="self-center">-</span>
            <input type="date" 
                   id="end-date" 
                   class="input input-bordered input-sm"
                   value="{{ end_date }}">
            <button class="btn btn-primary btn-sm" 
                    hx-get="{% url 'dashboard' %}"
                    hx-include="#start-date,#end-date"
                    hx-target="#dashboard-content">
                Filtrele
            </button>
        </div>
    </div>
    
    <div id="dashboard-content">
        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-sm">Toplam Müşteri</h2>
                    <p class="text-3xl font-bold text-primary">{{ total_customers }}</p>
                    <p class="text-sm text-gray-600">
                        <span class="text-green-600">+{{ new_customers }}</span> bu ay
                    </p>
                </div>
            </div>
            
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-sm">Toplam Gelir</h2>
                    <p class="text-3xl font-bold text-primary">${{ total_revenue|floatformat:2 }}</p>
                    <p class="text-sm text-gray-600">
                        <span class="{% if revenue_change > 0 %}text-green-600{% else %}text-red-600{% endif %}">
                            {% if revenue_change > 0 %}+{% endif %}{{ revenue_change }}%
                        </span> geçen aya göre
                    </p>
                </div>
            </div>
            
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-sm">Aktif Siparişler</h2>
                    <p class="text-3xl font-bold text-primary">{{ active_orders }}</p>
                    <p class="text-sm text-gray-600">
                        <span class="text-orange-600">{{ pending_orders }}</span> beklemede
                    </p>
                </div>
            </div>
            
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title text-sm">Dönüşüm Oranı</h2>
                    <p class="text-3xl font-bold text-primary">{{ conversion_rate }}%</p>
                    <p class="text-sm text-gray-600">
                        Ziyaretçiden müşteriye
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <!-- Sales Trend -->
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title">Satış Trendi</h2>
                    <div id="sales-chart"></div>
                </div>
            </div>
            
            <!-- Category Distribution -->
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title">Kategori Dağılımı</h2>
                    <div id="category-chart"></div>
                </div>
            </div>
        </div>
        
        <!-- Map and Table -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Customer Map -->
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title">Müşteri Dağılımı</h2>
                    <div id="customer-map" style="height: 400px;"></div>
                </div>
            </div>
            
            <!-- Recent Orders -->
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title">Son Siparişler</h2>
                    <div class="overflow-x-auto">
                        <table class="table table-compact w-full">
                            <thead>
                                <tr>
                                    <th>Sipariş No</th>
                                    <th>Müşteri</th>
                                    <th>Tutar</th>
                                    <th>Durum</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for order in recent_orders %}
                                <tr>
                                    <td>
                                        <a href="{% url 'order_detail' order.pk %}" class="link link-primary">
                                            {{ order.order_number }}
                                        </a>
                                    </td>
                                    <td>{{ order.customer.full_name }}</td>
                                    <td>${{ order.total_amount|floatformat:2 }}</td>
                                    <td>
                                        <span class="badge badge-{{ order.status|status_color }}">
                                            {{ order.get_status_display }}
                                        </span>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // ApexCharts - Sales Trend
    var salesOptions = {
        chart: {
            type: 'line',
            height: 350,
            toolbar: {
                show: false
            }
        },
        series: [{
            name: 'Satışlar',
            data: {{ sales_data|safe }}
        }],
        xaxis: {
            categories: {{ sales_labels|safe }}
        },
        colors: ['#22c55e'],
        stroke: {
            curve: 'smooth',
            width: 3
        }
    };
    
    var salesChart = new ApexCharts(document.querySelector("#sales-chart"), salesOptions);
    salesChart.render();
    
    // ApexCharts - Category Distribution
    var categoryOptions = {
        chart: {
            type: 'donut',
            height: 350
        },
        series: {{ category_data|safe }},
        labels: {{ category_labels|safe }},
        colors: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
    };
    
    var categoryChart = new ApexCharts(document.querySelector("#category-chart"), categoryOptions);
    categoryChart.render();
    
    // Leaflet Map
    var map = L.map('customer-map').setView([39.925533, 32.866287], 6);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Customer locations
    {% for customer in customer_locations %}
    L.marker([{{ customer.latitude }}, {{ customer.longitude }}])
        .addTo(map)
        .bindPopup('<b>{{ customer.full_name }}</b><br>{{ customer.city }}');
    {% endfor %}
</script>
{% endblock %}
```

---

## 9. API Documentation

### 9.1 Authentication Endpoints

```yaml
POST /api/auth/login/
  Request:
    {
      "username": "string",
      "password": "string"
    }
  Response:
    {
      "token": "string",
      "user": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "first_name": "string",
        "last_name": "string"
      }
    }

POST /api/auth/logout/
  Headers:
    Authorization: Token {token}
  Response:
    {
      "detail": "Successfully logged out."
    }

POST /api/auth/password/reset/
  Request:
    {
      "email": "string"
    }
  Response:
    {
      "detail": "Password reset e-mail has been sent."
    }
```

### 9.2 Customer Endpoints

```yaml
GET /api/customers/
  Query Parameters:
    - page: integer
    - search: string
    - status: string
    - assigned_to: integer
  Response:
    {
      "count": "integer",
      "next": "string",
      "previous": "string",
      "results": [
        {
          "id": "integer",
          "first_name": "string",
          "last_name": "string",
          "email": "string",
          "phone": "string",
          "company_name": "string",
          "status": "string",
          "created_at": "datetime"
        }
      ]
    }

POST /api/customers/
  Request:
    {
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "phone": "string",
      "company_name": "string",
      "status": "string"
    }
  Response:
    {
      "id": "integer",
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "created_at": "datetime"
    }

GET /api/customers/{id}/
  Response:
    {
      "id": "integer",
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "phone": "string",
      "company_name": "string",
      "title": "string",
      "address": "string",
      "city": "string",
      "state": "string",
      "postal_code": "string",
      "country": "string",
      "status": "string",
      "notes": "string",
      "created_at": "datetime",
      "updated_at": "datetime"
    }

PUT /api/customers/{id}/
  Request:
    {
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "status": "string"
    }
  Response:
    {
      "id": "integer",
      "first_name": "string",
      "last_name": "string",
      "updated_at": "datetime"
    }

DELETE /api/customers/{id}/
  Response:
    Status 204 No Content

GET /api/customers/statistics/
  Response:
    {
      "total_customers": "integer",
      "active_customers": "integer",
      "leads": "integer",
      "by_status": [
        {
          "status": "string",
          "count": "integer"
        }
      ],
      "by_country": [
        {
          "country": "string",
          "count": "integer"
        }
      ]
    }
```

### 9.3 Product Endpoints

```yaml
GET /api/products/
  Query Parameters:
    - page: integer
    - search: string
    - category: integer
    - status: string
    - in_stock: boolean
  Response:
    {
      "count": "integer",
      "next": "string",
      "previous": "string",
      "results": [
        {
          "id": "integer",
          "name": "string",
          "sku": "string",
          "price": "decimal",
          "stock_quantity": "integer",
          "category": {
            "id": "integer",
            "name": "string"
          },
          "status": "string"
        }
      ]
    }

POST /api/products/
  Request:
    {
      "name": "string",
      "sku": "string",
      "description": "string",
      "price": "decimal",
      "cost": "decimal",
      "category": "integer",
      "stock_quantity": "integer",
      "status": "string"
    }
  Response:
    {
      "id": "integer",
      "name": "string",
      "sku": "string",
      "price": "decimal",
      "created_at": "datetime"
    }

GET /api/products/{id}/
  Response:
    {
      "id": "integer",
      "name": "string",
      "sku": "string",
      "description": "string",
      "price": "decimal",
      "cost": "decimal",
      "discount_percentage": "decimal",
      "discounted_price": "decimal",
      "stock_quantity": "integer",
      "low_stock_threshold": "integer",
      "in_stock": "boolean",
      "low_stock": "boolean",
      "category": {
        "id": "integer",
        "name": "string"
      },
      "status": "string",
      "featured_image": "string",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
```

### 9.4 Order Endpoints

```yaml
GET /api/orders/
  Query Parameters:
    - page: integer
    - customer: integer
    - status: string
    - payment_status: string
    - date_from: date
    - date_to: date
  Response:
    {
      "count": "integer",
      "next": "string",
      "previous": "string",
      "results": [
        {
          "id": "integer",
          "order_number": "string",
          "customer": {
            "id": "integer",
            "full_name": "string"
          },
          "order_date": "datetime",
          "status": "string",
          "payment_status": "string",
          "total_amount": "decimal"
        }
      ]
    }

POST /api/orders/
  Request:
    {
      "customer": "integer",
      "status": "string",
      "payment_method": "string",
      "shipping_address": "string",
      "shipping_city": "string",
      "shipping_state": "string",
      "shipping_postal_code": "string",
      "shipping_country": "string",
      "billing_address": "string",
      "billing_city": "string",
      "billing_state": "string",
      "billing_postal_code": "string",
      "billing_country": "string",
      "items": [
        {
          "product": "integer",
          "quantity": "integer",
          "unit_price": "decimal"
        }
      ]
    }
  Response:
    {
      "id": "integer",
      "order_number": "string",
      "customer": "integer",
      "total_amount": "decimal",
      "created_at": "datetime"
    }

GET /api/orders/{id}/
  Response:
    {
      "id": "integer",
      "order_number": "string",
      "customer": {
        "id": "integer",
        "full_name": "string",
        "email": "string"
      },
      "order_date": "datetime",
      "status": "string",
      "payment_status": "string",
      "payment_method": "string",
      "shipping_address": "string",
      "shipping_city": "string",
      "shipping_state": "string",
      "shipping_postal_code": "string",
      "shipping_country": "string",
      "billing_address": "string",
      "billing_city": "string",
      "billing_state": "string",
      "billing_postal_code": "string",
      "billing_country": "string",
      "subtotal": "decimal",
      "tax_amount": "decimal",
      "shipping_amount": "decimal",
      "discount_amount": "decimal",
      "total_amount": "decimal",
      "items": [
        {
          "id": "integer",
          "product": {
            "id": "integer",
            "name": "string",
            "sku": "string"
          },
          "quantity": "integer",
          "unit_price": "decimal",
          "total_price": "decimal"
        }
      ],
      "created_at": "datetime",
      "updated_at": "datetime"
    }

PUT /api/orders/{id}/
  Request:
    {
      "status": "string",
      "payment_status": "string",
      "shipping_amount": "decimal",
      "notes": "string"
    }
  Response:
    {
      "id": "integer",
      "order_number": "string",
      "status": "string",
      "updated_at": "datetime"
    }

POST /api/orders/{id}/cancel/
  Response:
    {
      "detail": "Order cancelled successfully"
    }

POST /api/orders/{id}/refund/
  Request:
    {
      "amount": "decimal",
      "reason": "string"
    }
  Response:
    {
      "detail": "Refund processed successfully"
    }
```

### 9.5 Dashboard Endpoints

```yaml
GET /api/dashboard/summary/
  Query Parameters:
    - date_from: date
    - date_to: date
  Response:
    {
      "total_customers": "integer",
      "new_customers": "integer",
      "total_revenue": "decimal",
      "revenue_change": "decimal",
      "active_orders": "integer",
      "pending_orders": "integer",
      "conversion_rate": "decimal",
      "average_order_value": "decimal"
    }

GET /api/dashboard/sales-trend/
  Query Parameters:
    - period: string (daily|weekly|monthly)
    - date_from: date
    - date_to: date
  Response:
    {
      "labels": ["string"],
      "data": ["decimal"]
    }

GET /api/dashboard/category-distribution/
  Response:
    {
      "labels": ["string"],
      "data": ["decimal"]
    }

GET /api/dashboard/customer-locations/
  Response:
    [
      {
        "id": "integer",
        "full_name": "string",
        "city": "string",
        "latitude": "decimal",
        "longitude": "decimal",
        "total_orders": "integer",
        "total_revenue": "decimal"
      }
    ]

GET /api/dashboard/recent-orders/
  Query Parameters:
    - limit: integer (default: 10)
  Response:
    [
      {
        "id": "integer",
        "order_number": "string",
        "customer": {
          "id": "integer",
          "full_name": "string"
        },
        "total_amount": "decimal",
        "status": "string",
        "order_date": "datetime"
      }
    ]
```

### 9.6 Report Endpoints

```yaml
GET /api/reports/sales/
  Query Parameters:
    - date_from: date
    - date_to: date
    - group_by: string (day|week|month|year)
  Response:
    {
      "summary": {
        "total_sales": "decimal",
        "total_orders": "integer",
        "average_order_value": "decimal"
      },
      "data": [
        {
          "period": "string",
          "sales": "decimal",
          "orders": "integer"
        }
      ]
    }

GET /api/reports/products/
  Query Parameters:
    - date_from: date
    - date_to: date
    - category: integer
    - limit: integer
  Response:
    {
      "top_selling": [
        {
          "product": {
            "id": "integer",
            "name": "string",
            "sku": "string"
          },
          "units_sold": "integer",
          "revenue": "decimal"
        }
      ],
      "low_stock": [
        {
          "product": {
            "id": "integer",
            "name": "string",
            "sku": "string"
          },
          "stock_quantity": "integer",
          "low_stock_threshold": "integer"
        }
      ]
    }

GET /api/reports/customers/
  Query Parameters:
    - date_from: date
    - date_to: date
    - status: string
  Response:
    {
      "total_customers": "integer",
      "new_customers": "integer",
      "customer_lifetime_value": "decimal",
      "churn_rate": "decimal",
      "top_customers": [
        {
          "customer": {
            "id": "integer",
            "full_name": "string"
          },
          "total_orders": "integer",
          "total_spent": "decimal",
          "average_order_value": "decimal"
        }
      ]
    }

POST /api/reports/export/
  Request:
    {
      "report_type": "string",
      "format": "string" (excel|pdf),
      "filters": {
        "date_from": "date",
        "date_to": "date"
      }
    }
  Response:
    {
      "download_url": "string",
      "expires_at": "datetime"
    }
```

---

## 10. Development Workflow

### 10.1 Git Workflow

```bash
# Create feature branch
git checkout -b feature/customer-import

# Regular commits
git add .
git commit -m "feat: add customer Excel import functionality"

# Push to remote
git push origin feature/customer-import

# Create pull request
# Review and merge
```

### 10.2 Development Environment Setup

```bash
# Clone repository
git clone https://github.com/yourorg/vivacrm-v2.git
cd vivacrm-v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py loaddata fixtures/sample_data.json

# Run development server
python manage.py runserver

# In another terminal, run Celery
celery -A core worker -l info

# In another terminal, run Celery Beat
celery -A core beat -l info
```

### 10.3 Frontend Development

```bash
# Install Node dependencies
npm install

# Watch CSS changes
npm run watch:css

# Build production CSS
npm run build:css

# Format code
npm run format
```

### 10.4 Database Migrations

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate app_name migration_name
```

### 10.5 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_customers.py

# Run with coverage
pytest --cov=.

# Generate coverage report
pytest --cov=. --cov-report=html

# Run specific test class
pytest tests/test_customers.py::TestCustomerViews

# Run with verbose output
pytest -v

# Run only marked tests
pytest -m slow
```

---

## 11. Testing Strategy

### 11.1 Backend Testing

```python
# tests/test_customer_views.py
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from customers.models import Customer

User = get_user_model()

@pytest.mark.django_db
class TestCustomerViews:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.client.login(username='testuser', password='testpass')
    
    def test_customer_list_view(self):
        """Test customer list view"""
        response = self.client.get(reverse('customer_list'))
        assert response.status_code == 200
        assert 'page_obj' in response.context
    
    def test_customer_create_htmx(self):
        """Test HTMX customer creation"""
        response = self.client.post(
            reverse('customer_create'),
            data={
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'status': 'lead'
            },
            HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 204
        assert Customer.objects.filter(email='john@example.com').exists()
    
    def test_customer_search(self):
        """Test customer search functionality"""
        Customer.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com'
        )
        
        response = self.client.get(
            reverse('customer_list'),
            {'search': 'jane'}
        )
        
        assert response.status_code == 200
        assert 'Jane' in response.content.decode()
    
    def test_customer_detail_permissions(self):
        """Test customer detail view permissions"""
        customer = Customer.objects.create(
            first_name='Test',
            last_name='Customer',
            email='test@customer.com'
        )
        
        # Test with authenticated user
        response = self.client.get(
            reverse('customer_detail', args=[customer.pk])
        )
        assert response.status_code == 200
        
        # Test with unauthenticated user
        self.client.logout()
        response = self.client.get(
            reverse('customer_detail', args=[customer.pk])
        )
        assert response.status_code == 302  # Redirect to login
```

### 11.2 API Testing

```python
# tests/test_customer_api.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from customers.models import Customer

User = get_user_model()

@pytest.mark.django_db
class TestCustomerAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_customers(self):
        """Test GET /api/customers/"""
        Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        
        response = self.client.get('/api/customers/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
    
    def test_create_customer(self):
        """Test POST /api/customers/"""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'status': 'lead'
        }
        
        response = self.client.post('/api/customers/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Customer.objects.filter(email='jane@example.com').exists()
    
    def test_update_customer(self):
        """Test PUT /api/customers/{id}/"""
        customer = Customer.objects.create(
            first_name='Original',
            last_name='Name',
            email='original@example.com'
        )
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'status': 'customer'
        }
        
        response = self.client.put(f'/api/customers/{customer.pk}/', data)
        assert response.status_code == status.HTTP_200_OK
        
        customer.refresh_from_db()
        assert customer.first_name == 'Updated'
        assert customer.email == 'updated@example.com'
    
    def test_customer_statistics(self):
        """Test GET /api/customers/statistics/"""
        # Create test data
        for i in range(5):
            Customer.objects.create(
                first_name=f'Customer{i}',
                last_name='Test',
                email=f'customer{i}@example.com',
                status='lead' if i < 3 else 'customer'
            )
        
        response = self.client.get('/api/customers/statistics/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_customers'] == 5
        assert response.data['leads'] == 3
        assert response.data['active_customers'] == 2
```

### 11.3 Frontend Testing

```javascript
// static/js/tests/customer.test.js
describe('Customer Module', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="customer-table-container"></div>
            <div id="modal-container"></div>
        `;
    });
    
    test('HTMX trigger updates table', () => {
        // Test HTMX event trigger
        const event = new CustomEvent('customerListChanged');
        document.body.dispatchEvent(event);
        
        // Verify HTMX trigger
        expect(htmx.trigger).toHaveBeenCalledWith(
            '#customer-table-container',
            'htmx:afterSettle'
        );
    });
    
    test('Search input debounces requests', (done) => {
        const searchInput = document.createElement('input');
        searchInput.setAttribute('hx-get', '/customers/');
        searchInput.setAttribute('hx-trigger', 'keyup changed delay:500ms');
        document.body.appendChild(searchInput);
        
        // Simulate rapid typing
        searchInput.value = 'j';
        searchInput.dispatchEvent(new Event('keyup'));
        
        searchInput.value = 'jo';
        searchInput.dispatchEvent(new Event('keyup'));
        
        searchInput.value = 'joh';
        searchInput.dispatchEvent(new Event('keyup'));
        
        // Check that only one request is made after delay
        setTimeout(() => {
            expect(htmx.ajax).toHaveBeenCalledTimes(1);
            done();
        }, 600);
    });
});
```

### 11.4 E2E Testing

```python
# tests/e2e/test_customer_flow.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

@pytest.mark.e2e
class TestCustomerFlow:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.get('http://localhost:8000')
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_complete_customer_flow(self):
        """Test complete customer creation and management flow"""
        # Login
        username_input = self.driver.find_element(By.NAME, 'username')
        password_input = self.driver.find_element(By.NAME, 'password')
        login_button = self.driver.find_element(By.XPATH, '//button[text()="GİRİŞ YAP"]')
        
        username_input.send_keys('admin')
        password_input.send_keys('admin123')
        login_button.click()
        
        # Navigate to customers
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Müşteriler'))).click()
        
        # Create new customer
        new_customer_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Yeni Müşteri")]'))
        )
        new_customer_button.click()
        
        # Fill form
        first_name = self.wait.until(EC.element_to_be_clickable((By.NAME, 'first_name')))
        first_name.send_keys('Test')
        
        last_name = self.driver.find_element(By.NAME, 'last_name')
        last_name.send_keys('Customer')
        
        email = self.driver.find_element(By.NAME, 'email')
        email.send_keys('test@customer.com')
        
        # Submit form
        submit_button = self.driver.find_element(By.XPATH, '//button[text()="Kaydet"]')
        submit_button.click()
        
        # Verify customer created
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.XPATH, '//table//td'),
                'Test Customer'
            )
        )
        
        # Search for customer
        search_input = self.driver.find_element(By.NAME, 'search')
        search_input.send_keys('test@customer.com')
        
        # Verify search results
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.XPATH, '//table//td'),
                'test@customer.com'
            )
        )
```

---

## 12. Deployment Guide

### 12.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Start server
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 12.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: vivacrm
      POSTGRES_USER: vivacrm
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  web:
    build: .
    environment:
      DATABASE_URL: postgresql://vivacrm:${DB_PASSWORD}@postgres:5432/vivacrm
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000
  
  celery:
    build: .
    environment:
      DATABASE_URL: postgresql://vivacrm:${DB_PASSWORD}@postgres:5432/vivacrm
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: celery -A core worker -l info
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### 12.3 Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location /static/ {
        alias /app/staticfiles/;
    }
    
    location /media/ {
        alias /app/media/;
    }
    
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 12.4 Production Environment Variables

```bash
# .env.production
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=user@example.com
EMAIL_HOST_PASSWORD=password
EMAIL_USE_TLS=True
```

### 12.5 Deployment Checklist

```markdown
## Pre-Deployment
- [ ] Run all tests
- [ ] Update requirements.txt
- [ ] Check for security vulnerabilities
- [ ] Update environment variables
- [ ] Review code for production readiness
- [ ] Create database backup

## Deployment Steps
1. [ ] Push code to production branch
2. [ ] Pull latest code on server
3. [ ] Update environment variables
4. [ ] Build Docker images
5. [ ] Run database migrations
6. [ ] Collect static files
7. [ ] Restart services
8. [ ] Run smoke tests

## Post-Deployment
- [ ] Verify all services are running
- [ ] Check error logs
- [ ] Test critical user flows
- [ ] Monitor performance metrics
- [ ] Update documentation
- [ ] Notify team of deployment
```

---

## 13. Additional Development Guidelines

### 13.1 Code Style Guide

```python
# Python Style Guide (PEP 8)

# Imports
import os
import sys
from datetime import datetime

from django.db import models
from django.contrib.auth import get_user_model

from .models import Customer
from .forms import CustomerForm


# Constants
MAX_NAME_LENGTH = 100
DEFAULT_STATUS = 'lead'


# Classes
class CustomerManager(models.Manager):
    """
    Custom manager for Customer model.
    Provides additional query methods.
    """
    
    def active(self):
        """Return only active customers."""
        return self.filter(status='customer')
    
    def leads(self):
        """Return only leads."""
        return self.filter(status='lead')


# Functions
def calculate_customer_value(customer):
    """
    Calculate the lifetime value of a customer.
    
    Args:
        customer: Customer instance
        
    Returns:
        Decimal: Total lifetime value
    """
    total_value = customer.orders.aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0
    
    return total_value


# Django specific
class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model.
    Includes calculated fields and nested relationships.
    """
    
    full_name = serializers.SerializerMethodField()
    total_orders = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'company_name', 'status',
            'total_orders', 'created_at', 'updated_at'
        ]
    
    def get_full_name(self, obj):
        """Return the customer's full name."""
        return f"{obj.first_name} {obj.last_name}"
```

### 13.2 JavaScript Style Guide

```javascript
// JavaScript Style Guide

// Constants
const API_BASE_URL = '/api/v1';
const DEFAULT_TIMEOUT = 5000;

// Functions
function initializeCustomerTable() {
    /**
     * Initialize DataTable for customer list
     */
    const table = $('#customer-table').DataTable({
        responsive: true,
        pageLength: 25,
        order: [[0, 'desc']],
        columns: [
            { data: 'id' },
            { data: 'full_name' },
            { data: 'email' },
            { data: 'status' },
            { data: 'actions', orderable: false }
        ]
    });
    
    return table;
}

// Event Handlers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize HTMX event listeners
    document.body.addEventListener('customerListChanged', function() {
        htmx.trigger('#customer-table-container', 'htmx:afterSettle');
    });
    
    // Initialize Alpine.js components
    Alpine.data('customerForm', () => ({
        formData: {
            first_name: '',
            last_name: '',
            email: '',
            phone: ''
        },
        errors: {},
        
        submitForm() {
            fetch('/api/customers/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(this.formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.errors) {
                    this.errors = data.errors;
                } else {
                    // Success - trigger table refresh
                    document.body.dispatchEvent(
                        new CustomEvent('customerListChanged')
                    );
                    // Close modal
                    this.$dispatch('close-modal');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
    }));
});

// Utility Functions
function getCookie(name) {
    /**
     * Get CSRF token from cookies
     */
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// API Client
class VivaCRMClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
        this.headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        };
    }
    
    async get(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'GET',
            headers: this.headers
        });
        return response.json();
    }
    
    async post(endpoint, data) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return response.json();
    }
    
    async put(endpoint, data) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'PUT',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return response.json();
    }
    
    async delete(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'DELETE',
            headers: this.headers
        });
        return response.ok;
    }
}

// Export for use in other modules
export { VivaCRMClient, initializeCustomerTable };
```

### 13.3 HTML/Template Style Guide

```html
<!-- HTML/Django Template Style Guide -->

<!-- Base template structure -->
{% extends 'base.html' %}
{% load static %}
{% load i18n %}

{% block title %}{{ page_title }} - VivaCRM{% endblock %}

{% block extra_css %}
    <link rel="stylesheet" href="{% static 'css/customers.css' %}">
{% endblock %}

{% block content %}
<div class="container mx-auto px-4">
    <!-- Page Header -->
    <header class="page-header mb-6">
        <div class="flex justify-between items-center">
            <h1 class="text-3xl font-bold">{{ page_title }}</h1>
            
            <!-- Action Buttons -->
            <div class="flex gap-2">
                {% if user.has_perm('customers.add_customer') %}
                <button type="button" 
                        class="btn btn-primary"
                        hx-get="{% url 'customer_create' %}"
                        hx-target="#modal-container"
                        hx-trigger="click">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                    Yeni Müşteri
                </button>
                {% endif %}
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <main class="main-content">
        {% if messages %}
        <div class="messages mb-4">
            {% for message in messages %}
            <div class="alert alert-{{ message.tags }}">
                {{ message }}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <!-- Content Section -->
        <section class="content-section">
            {% block section_content %}
            <!-- Dynamic content loaded here -->
            {% endblock %}
        </section>
    </main>
</div>

<!-- Modal Container -->
<div id="modal-container"></div>

<!-- Loading Indicator -->
<div id="loading-indicator" class="htmx-indicator">
    <div class="loading loading-spinner loading-lg"></div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/customers.js' %}"></script>
<script>
    // Page-specific JavaScript
    document.addEventListener('DOMContentLoaded', function() {
        initializeCustomerTable();
    });
</script>
{% endblock %}

<!-- Component Examples -->

<!-- Card Component -->
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">{{ card_title }}</h2>
        <p>{{ card_content }}</p>
        <div class="card-actions justify-end">
            <button class="btn btn-primary">{{ action_text }}</button>
        </div>
    </div>
</div>

<!-- Table Component -->
<div class="overflow-x-auto">
    <table class="table w-full">
        <thead>
            <tr>
                <th>ID</th>
                <th>Ad Soyad</th>
                <th>Email</th>
                <th>Durum</th>
                <th>İşlemler</th>
            </tr>
        </thead>
        <tbody>
            {% for customer in customers %}
            <tr class="hover">
                <td>{{ customer.id }}</td>
                <td>{{ customer.full_name }}</td>
                <td>{{ customer.email|default:"-" }}</td>
                <td>
                    <span class="badge badge-{{ customer.status|status_color }}">
                        {{ customer.get_status_display }}
                    </span>
                </td>
                <td>
                    <div class="flex gap-2">
                        <a href="{% url 'customer_detail' customer.pk %}" 
                           class="btn btn-ghost btn-sm">
                            Detay
                        </a>
                        <button type="button"
                                class="btn btn-ghost btn-sm"
                                hx-get="{% url 'customer_edit' customer.pk %}"
                                hx-target="#modal-container"
                                hx-trigger="click">
                            Düzenle
                        </button>
                    </div>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="5" class="text-center text-gray-500 py-8">
                    Kayıt bulunamadı.
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- Form Component -->
<form method="post" 
      action="{% url 'customer_create' %}"
      hx-post="{% url 'customer_create' %}"
      hx-target="#modal-container"
      hx-swap="innerHTML"
      class="space-y-4">
    {% csrf_token %}
    
    <div class="form-control">
        <label class="label">
            <span class="label-text">Ad</span>
            <span class="label-text-alt text-error">*</span>
        </label>
        <input type="text" 
               name="first_name" 
               value="{{ form.first_name.value|default:'' }}"
               class="input input-bordered {% if form.first_name.errors %}input-error{% endif %}"
               required>
        {% if form.first_name.errors %}
        <label class="label">
            <span class="label-text-alt text-error">
                {{ form.first_name.errors.0 }}
            </span>
        </label>
        {% endif %}
    </div>
    
    <div class="form-control">
        <label class="label">
            <span class="label-text">Email</span>
        </label>
        <input type="email" 
               name="email" 
               value="{{ form.email.value|default:'' }}"
               class="input input-bordered {% if form.email.errors %}input-error{% endif %}">
        {% if form.email.errors %}
        <label class="label">
            <span class="label-text-alt text-error">
                {{ form.email.errors.0 }}
            </span>
        </label>
        {% endif %}
    </div>
    
    <div class="modal-action">
        <button type="button" 
                class="btn"
                onclick="closeModal()">
            İptal
        </button>
        <button type="submit" 
                class="btn btn-primary">
            Kaydet
        </button>
    </div>
</form>
```

### 13.4 Database Query Optimization

```python
# Database Query Optimization Examples

# Bad: N+1 query problem
customers = Customer.objects.all()
for customer in customers:
    print(customer.orders.count())  # This creates a new query for each customer

# Good: Use annotate
from django.db.models import Count
customers = Customer.objects.annotate(order_count=Count('orders'))
for customer in customers:
    print(customer.order_count)  # No additional queries

# Bad: Loading unnecessary fields
customers = Customer.objects.all()

# Good: Use only() or defer()
customers = Customer.objects.only('id', 'first_name', 'last_name', 'email')
customers = Customer.objects.defer('notes', 'created_at', 'updated_at')

# Bad: Multiple queries for related objects
orders = Order.objects.all()
for order in orders:
    print(order.customer.full_name)  # Query for each customer

# Good: Use select_related for ForeignKey
orders = Order.objects.select_related('customer')
for order in orders:
    print(order.customer.full_name)  # No additional queries

# Good: Use prefetch_related for ManyToMany
orders = Order.objects.prefetch_related('items__product')
for order in orders:
    for item in order.items.all():
        print(item.product.name)  # No additional queries

# Complex query optimization
from django.db.models import Prefetch, Sum, F, Q

# Optimize dashboard statistics
def get_dashboard_stats(date_from, date_to):
    # Use aggregation instead of looping
    stats = {
        'total_revenue': Order.objects.filter(
            order_date__range=[date_from, date_to],
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        
        'customer_count': Customer.objects.filter(
            created_at__range=[date_from, date_to]
        ).count(),
        
        'top_products': Product.objects.filter(
            orderitem__order__order_date__range=[date_from, date_to]
        ).annotate(
            units_sold=Sum('orderitem__quantity'),
            revenue=Sum(F('orderitem__quantity') * F('orderitem__unit_price'))
        ).order_by('-units_sold')[:10]
    }
    
    return stats

# Use database functions
from django.db.models.functions import TruncMonth

monthly_sales = Order.objects.filter(
    order_date__year=2024
).annotate(
    month=TruncMonth('order_date')
).values('month').annotate(
    total_sales=Sum('total_amount'),
    order_count=Count('id')
).order_by('month')
```

### 13.5 Security Best Practices

```python
# Security Best Practices

# 1. Input Validation
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

def validate_customer_data(data):
    """Validate customer input data."""
    errors = {}
    
    # Email validation
    if data.get('email'):
        try:
            validate_email(data['email'])
        except ValidationError:
            errors['email'] = 'Invalid email format'
    
    # Phone validation
    phone = data.get('phone', '')
    if phone and not phone.replace('+', '').replace('-', '').isdigit():
        errors['phone'] = 'Phone number must contain only digits'
    
    # SQL injection prevention (Django ORM handles this)
    # Always use parameterized queries
    Customer.objects.filter(email=data['email'])  # Safe
    # Customer.objects.raw(f"SELECT * FROM customers WHERE email = '{email}'")  # Unsafe
    
    return errors

# 2. Authentication & Authorization
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied

@login_required
@permission_required('customers.view_customer', raise_exception=True)
def customer_detail(request, pk):
    """View customer details with permission check."""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Additional authorization check
    if not request.user.is_staff and customer.assigned_to != request.user:
        raise PermissionDenied("You don't have permission to view this customer.")
    
    return render(request, 'customers/detail.html', {'customer': customer})

# 3. CSRF Protection
# Always include {% csrf_token %} in forms
# For AJAX requests, include CSRF token in headers

# 4. File Upload Security
from django.core.exceptions import ValidationError
import os

def validate_file_extension(value):
    """Validate uploaded file extensions."""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError(f'Unsupported file extension: {ext}')

# 5. SQL Injection Prevention
# Always use Django ORM or parameterized queries
from django.db import connection

def get_customer_by_email(email):
    # Safe: Parameterized query
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM customers WHERE email = %s",
            [email]
        )
        return cursor.fetchone()

# 6. XSS Prevention
# Django automatically escapes template variables
# Use |safe filter only when necessary and with trusted content
# For user input, always validate and sanitize

from django.utils.html import escape

def save_customer_note(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    note = request.POST.get('note', '')
    
    # Sanitize user input
    customer.notes = escape(note)
    customer.save()
    
    return JsonResponse({'success': True})

# 7. Password Security
from django.contrib.auth.password_validation import validate_password

def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        
        try:
            validate_password(new_password, request.user)
            request.user.set_password(new_password)
            request.user.save()
            return JsonResponse({'success': True})
        except ValidationError as e:
            return JsonResponse({'errors': e.messages}, status=400)

# 8. Session Security
# settings.py
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# 9. Rate Limiting
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests

def rate_limit_view(request):
    # Rate limit: 10 requests per minute per IP
    ip = request.META.get('REMOTE_ADDR')
    cache_key = f'rate-limit-{ip}'
    
    requests = cache.get(cache_key, 0)
    if requests >= 10:
        return HttpResponseTooManyRequests("Too many requests")
    
    cache.set(cache_key, requests + 1, 60)  # 60 seconds
    
    # Process request
    return JsonResponse({'data': 'success'})

# 10. Content Security Policy
# middleware.py
class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
        )
        return response
```

### 13.6 Performance Monitoring

```python
# Performance Monitoring

# 1. Database Query Logging
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/db_queries.log',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['file'],
        },
    },
}

# 2. Custom Middleware for Request Timing
import time
import logging

logger = logging.getLogger(__name__)

class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        logger.info(f"{request.method} {request.path} - {duration:.3f}s")
        
        if duration > 1.0:  # Log slow requests
            logger.warning(f"Slow request: {request.method} {request.path} - {duration:.3f}s")
        
        return response

# 3. Caching Strategy
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# View-level caching
@cache_page(60 * 15)  # Cache for 15 minutes
def product_list(request):
    products = Product.objects.filter(status='active')
    return render(request, 'products/list.html', {'products': products})

# Function-level caching
def get_top_selling_products(limit=10):
    cache_key = f'top_selling_products_{limit}'
    result = cache.get(cache_key)
    
    if result is None:
        result = Product.objects.annotate(
            units_sold=Sum('orderitem__quantity')
        ).order_by('-units_sold')[:limit]
        
        cache.set(cache_key, result, 60 * 60)  # Cache for 1 hour
    
    return result

# 4. Database Connection Pooling
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vivacrm',
        'USER': 'vivacrm',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# 5. Query Optimization with Debug Toolbar
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# 6. Celery Task Performance
from celery import shared_task
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, time_limit=300)  # 5 minute timeout
def generate_sales_report(self, date_from, date_to):
    """Generate sales report with progress tracking."""
    try:
        # Track progress
        total_steps = 4
        current_step = 0
        
        def update_progress(step):
            progress = int((step / total_steps) * 100)
            cache.set(f'task_progress_{self.request.id}', progress, 300)
        
        # Step 1: Gather data
        update_progress(1)
        orders = Order.objects.filter(
            order_date__range=[date_from, date_to]
        ).select_related('customer').prefetch_related('items__product')
        
        # Step 2: Calculate statistics
        update_progress(2)
        stats = calculate_sales_statistics(orders)
        
        # Step 3: Generate report
        update_progress(3)
        report = generate_excel_report(stats)
        
        # Step 4: Save and notify
        update_progress(4)
        report_url = save_report(report)
        
        return {
            'status': 'success',
            'report_url': report_url
        }
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

# 7. API Rate Limiting
from rest_framework.throttling import UserRateThrottle

class CustomerAPIThrottle(UserRateThrottle):
    rate = '100/hour'

class CustomerViewSet(viewsets.ModelViewSet):
    throttle_classes = [CustomerAPIThrottle]
    # ... rest of viewset code
```

### 13.7 Error Handling and Logging

```python
# Error Handling and Logging

# 1. Custom Error Pages
# views.py
from django.shortcuts import render

def handler404(request, exception):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error page."""
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    """Custom 403 error page."""
    return render(request, 'errors/403.html', status=403)

# urls.py
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
handler403 = 'core.views.handler403'

# 2. Comprehensive Logging Setup
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'vivacrm': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# 3. Error Tracking with Sentry (optional)
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment="production"
)

# 4. Custom Exception Classes
class VivaCRMException(Exception):
    """Base exception for VivaCRM."""
    pass

class CustomerNotFoundException(VivaCRMException):
    """Raised when customer not found."""
    pass

class InsufficientStockException(VivaCRMException):
    """Raised when product stock is insufficient."""
    pass

class PaymentProcessingException(VivaCRMException):
    """Raised when payment processing fails."""
    pass

# 5. Error Handling in Views
from django.http import JsonResponse
import logging

logger = logging.getLogger('vivacrm')

def create_order(request):
    try:
        # Process order creation
        order_data = json.loads(request.body)
        
        # Validate customer
        customer = Customer.objects.get(pk=order_data['customer_id'])
        
        # Check stock availability
        for item in order_data['items']:
            product = Product.objects.get(pk=item['product_id'])
            if product.stock_quantity < item['quantity']:
                raise InsufficientStockException(
                    f"Insufficient stock for {product.name}"
                )
        
        # Create order
        order = Order.objects.create(
            customer=customer,
            status='pending'
        )
        
        # Process payment
        payment_result = process_payment(order, order_data['payment_info'])
        if not payment_result['success']:
            raise PaymentProcessingException(payment_result['error'])
        
        # Create order items
        for item in order_data['items']:
            OrderItem.objects.create(
                order=order,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            )
        
        # Update stock
        for item in order_data['items']:
            product = Product.objects.get(pk=item['product_id'])
            product.stock_quantity -= item['quantity']
            product.save()
        
        # Calculate totals
        order.calculate_total()
        
        logger.info(f"Order {order.order_number} created successfully")
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number
        })
        
    except Customer.DoesNotExist:
        logger.error(f"Customer not found: {order_data.get('customer_id')}")
        return JsonResponse({
            'error': 'Customer not found'
        }, status=404)
        
    except Product.DoesNotExist:
        logger.error(f"Product not found")
        return JsonResponse({
            'error': 'Product not found'
        }, status=404)
        
    except InsufficientStockException as e:
        logger.warning(f"Insufficient stock: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
        
    except PaymentProcessingException as e:
        logger.error(f"Payment processing failed: {str(e)}")
        # Rollback order creation
        if 'order' in locals():
            order.delete()
        return JsonResponse({
            'error': 'Payment processing failed'
        }, status=400)
        
    except Exception as e:
        logger.exception(f"Unexpected error in create_order: {str(e)}")
        return JsonResponse({
            'error': 'An unexpected error occurred'
        }, status=500)

# 6. Centralized Error Response
def error_response(message, status_code=400, errors=None):
    """Create standardized error response."""
    response_data = {
        'success': False,
        'message': message
    }
    
    if errors:
        response_data['errors'] = errors
    
    return JsonResponse(response_data, status=status_code)

# 7. Form Error Handling
from django.forms import ValidationError

class CustomerForm(forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check for duplicate email
            existing = Customer.objects.filter(
                email=email
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise ValidationError('A customer with this email already exists.')
        
        return email
    
    def save(self, commit=True):
        try:
            customer = super().save(commit=False)
            if commit:
                customer.save()
                logger.info(f"Customer {customer.full_name} saved successfully")
            return customer
        except Exception as e:
            logger.error(f"Error saving customer: {str(e)}")
            raise

# 8. Async Error Handling (Celery)
@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def send_order_confirmation_email(self, order_id):
    """Send order confirmation email with retry logic."""
    try:
        order = Order.objects.get(pk=order_id)
        
        # Send email
        send_mail(
            subject=f'Order Confirmation - {order.order_number}',
            message=render_to_string('emails/order_confirmation.txt', {'order': order}),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            html_message=render_to_string('emails/order_confirmation.html', {'order': order})
        )
        
        logger.info(f"Order confirmation email sent for {order.order_number}")
        return True
        
    except Order.DoesNotExist:
        logger.error(f"Order not found: {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error sending order confirmation: {str(e)}")
        # Will retry automatically
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute

# 9. Frontend Error Handling
// static/js/error-handler.js
class ErrorHandler {
    static showError(message, duration = 5000) {
        const toast = document.createElement('div');
        toast.className = 'toast toast-top toast-end';
        toast.innerHTML = `
            <div class="alert alert-error">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
    
    static handleAjaxError(xhr) {
        let message = 'An error occurred';
        
        try {
            const response = JSON.parse(xhr.responseText);
            message = response.message || response.error || message;
        } catch (e) {
            if (xhr.status === 404) {
                message = 'Resource not found';
            } else if (xhr.status === 403) {
                message = 'Permission denied';
            } else if (xhr.status === 500) {
                message = 'Server error occurred';
            }
        }
        
        this.showError(message);
    }
    
    static handleFormErrors(form, errors) {
        // Clear previous errors
        form.querySelectorAll('.error-message').forEach(el => el.remove());
        form.querySelectorAll('.input-error').forEach(el => {
            el.classList.remove('input-error');
        });
        
        // Display new errors
        Object.keys(errors).forEach(field => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                input.classList.add('input-error');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-error text-sm mt-1 error-message';
                errorDiv.textContent = errors[field][0];
                
                input.parentElement.appendChild(errorDiv);
            }
        });
    }
}

// HTMX error handling
document.addEventListener('htmx:responseError', (event) => {
    ErrorHandler.handleAjaxError(event.detail.xhr);
});

// Global error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    ErrorHandler.showError('An unexpected error occurred');
});
```

### 13.8 Internationalization and Localization

```python
# Internationalization and Localization

# 1. Settings Configuration
# settings.py
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('tr', _('Turkish')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# 2. Model Translations
from django.utils.translation import gettext_lazy as _

class Customer(models.Model):
    STATUS_CHOICES = [
        ('lead', _('Lead')),
        ('prospect', _('Prospect')),
        ('customer', _('Customer')),
        ('inactive', _('Inactive')),
        ('archived', _('Archived'))
    ]
    
    first_name = models.CharField(_('First Name'), max_length=100)
    last_name = models.CharField(_('Last Name'), max_length=100)
    email = models.EmailField(_('Email'), unique=True, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
        ordering = ['-created_at']

# 3. View Translations
from django.utils.translation import gettext as _
from django.contrib import messages

def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, _('Customer created successfully.'))
            return redirect('customer_detail', pk=customer.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'page_title': _('Create Customer')
    }
    return render(request, 'customers/create.html', context)

# 4. Template Translations
# templates/customers/list.html
{% load i18n %}

<h1>{% trans "Customers" %}</h1>

<p>
    {% blocktrans count counter=customer_count %}
        {{ counter }} customer found.
    {% plural %}
        {{ counter }} customers found.
    {% endblocktrans %}
</p>

<table>
    <thead>
        <tr>
            <th>{% trans "Name" %}</th>
            <th>{% trans "Email" %}</th>
            <th>{% trans "Status" %}</th>
            <th>{% trans "Actions" %}</th>
        </tr>
    </thead>
</table>

# 5. JavaScript Translations
# static/js/translations.js
const translations = {
    tr: {
        'confirm_delete': 'Silmek istediğinizden emin misiniz?',
        'loading': 'Yükleniyor...',
        'error': 'Hata',
        'success': 'Başarılı',
        'save': 'Kaydet',
        'cancel': 'İptal',
        'delete': 'Sil',
        'edit': 'Düzenle',
        'create': 'Oluştur',
        'search': 'Ara',
        'no_results': 'Sonuç bulunamadı',
        'required_field': 'Bu alan zorunludur',
        'invalid_email': 'Geçersiz email adresi',
        'invalid_phone': 'Geçersiz telefon numarası'
    },
    en: {
        'confirm_delete': 'Are you sure you want to delete?',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'save': 'Save',
        'cancel': 'Cancel',
        'delete': 'Delete',
        'edit': 'Edit',
        'create': 'Create',
        'search': 'Search',
        'no_results': 'No results found',
        'required_field': 'This field is required',
        'invalid_email': 'Invalid email address',
        'invalid_phone': 'Invalid phone number'
    }
};

function getTranslation(key) {
    const lang = document.documentElement.lang || 'tr';
    return translations[lang][key] || key;
}

// Usage
if (confirm(getTranslation('confirm_delete'))) {
    // Delete action
}

# 6. Dynamic Language Switching
# views.py
from django.utils import translation
from django.conf import settings

def set_language(request):
    next_page = request.POST.get('next', request.GET.get('next'))
    if not next_page:
        next_page = request.META.get('HTTP_REFERER')
    if not next_page:
        next_page = '/'
    
    response = HttpResponseRedirect(next_page)
    
    if request.method == 'POST':
        language = request.POST.get('language')
        if language and language in dict(settings.LANGUAGES).keys():
            translation.activate(language)
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                language,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
    
    return response

# 7. Currency and Number Formatting
from django.utils.formats import localize
from babel.numbers import format_currency

def format_price(amount, currency='USD'):
    """Format price based on current locale."""
    locale = get_language()
    
    if locale == 'tr':
        # Turkish formatting
        return format_currency(amount, currency, locale='tr_TR')
    else:
        # Default to English
        return format_currency(amount, currency, locale='en_US')

# Template filter
@register.filter
def currency(value, currency='USD'):
    """Currency template filter."""
    return format_price(value, currency)

# Usage in template
# {{ product.price|currency:"USD" }}

# 8. Date and Time Formatting
from django.utils import timezone
from django.utils.formats import date_format

@register.filter
def formatted_date(value, format_string=None):
    """Format date based on current locale."""
    if not value:
        return ''
    
    if not format_string:
        # Use locale-specific default format
        return date_format(value, use_l10n=True)
    
    return date_format(value, format_string)

# 9. Locale-specific Validation
from django.core.validators import RegexValidator

phone_validator_tr = RegexValidator(
    regex=r'^\+90\d{10},
    message=_('Enter a valid Turkish phone number.')
)

phone_validator_us = RegexValidator(
    regex=r'^\+1\d{10},
    message=_('Enter a valid US phone number.')
)

class Customer(models.Model):
    phone = models.CharField(
        _('Phone'),
        max_length=20,
        validators=[phone_validator_tr],
        blank=True
    )

# 10. Translation Management Commands
# management/commands/update_translations.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Update all translation files'
    
    def handle(self, *args, **options):
        # Extract messages
        call_command('makemessages', all=True, ignore=['venv', 'node_modules'])
        
        # Compile messages
        call_command('compilemessages')
        
        self.stdout.write(self.style.SUCCESS('Successfully updated translations'))
```

### 13.9 Background Tasks and Scheduling

```python
# Background Tasks and Scheduling

# 1. Celery Configuration
# celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('vivacrm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery beat schedule
app.conf.beat_schedule = {
    'daily-report': {
        'task': 'reports.tasks.generate_daily_report',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8 AM
    },
    'check-low-stock': {
        'task': 'products.tasks.check_low_stock',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-old-sessions': {
        'task': 'core.tasks.cleanup_sessions',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2 AM
    },
    'send-monthly-newsletter': {
        'task': 'marketing.tasks.send_newsletter',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),  # First day of month at 9 AM
    },
}

# 2. Task Examples
# tasks.py
from celery import shared_task
from django.core.mail import send_mass_mail
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
import csv
import os

@shared_task
def generate_daily_report():
    """Generate daily sales report."""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Get sales data
    orders = Order.objects.filter(
        order_date__date=yesterday,
        status='delivered'
    )
    
    stats = {
        'date': yesterday,
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'average_order_value': orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0,
        'top_products': Product.objects.filter(
            orderitem__order__in=orders
        ).annotate(
            units_sold=Sum('orderitem__quantity')
        ).order_by('-units_sold')[:10]
    }
    
    # Generate PDF report
    pdf = generate_pdf_report(stats)
    
    # Send to managers
    managers = User.objects.filter(is_staff=True, is_active=True)
    for manager in managers:
        send_mail(
            subject=f'Daily Report - {yesterday}',
            message='Please find attached the daily sales report.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[manager.email],
            attachments=[('daily_report.pdf', pdf, 'application/pdf')]
        )
    
    return f"Daily report sent to {managers.count()} managers"

@shared_task
def check_low_stock():
    """Check for products with low stock and notify."""
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('low_stock_threshold'),
        status='active'
    )
    
    if low_stock_products.exists():
        # Prepare notification
        message = "The following products have low stock:\n\n"
        for product in low_stock_products:
            message += f"- {product.name} (SKU: {product.sku}): {product.stock_quantity} units\n"
        
        # Send notification
        send_mail(
            subject='Low Stock Alert',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.INVENTORY_MANAGER_EMAIL]
        )
        
        # Create system notification
        Notification.objects.create(
            type='low_stock',
            title='Low Stock Alert',
            message=f'{low_stock_products.count()} products have low stock',
            priority='high'
        )
    
    return f"Checked {Product.objects.count()} products, {low_stock_products.count()} have low stock"

@shared_task(bind=True)
def import_customers_from_csv(self, file_path):
    """Import customers from CSV file with progress tracking."""
    try:
        # Count total rows
        with open(file_path, 'r', encoding='utf-8') as file:
            total_rows = sum(1 for line in file) - 1  # Minus header
        
        # Process CSV
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in enumerate(reader):
                try:
                    # Create or update customer
                    customer, created = Customer.objects.update_or_create(
                        email=row['email'],
                        defaults={
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'phone': row.get('phone', ''),
                            'company_name': row.get('company', ''),
                            'address': row.get('address', ''),
                            'city': row.get('city', ''),
                            'state': row.get('state', ''),
                            'postal_code': row.get('postal_code', ''),
                            'country': row.get('country', 'USA'),
                        }
                    )
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index + 2}: {str(e)}")
                
                # Update progress
                if index % 100 == 0:
                    progress = int((index / total_rows) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': index, 'total': total_rows, 'percent': progress}
                    )
        
        # Clean up
        os.remove(file_path)
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # Return first 10 errors
        }
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

@shared_task
def send_order_reminders():
    """Send reminders for pending orders."""
    # Get orders pending for more than 3 days
    three_days_ago = timezone.now() - timedelta(days=3)
    pending_orders = Order.objects.filter(
        status='pending',
        created_at__lte=three_days_ago
    )
    
    messages = []
    for order in pending_orders:
        message = (
            f'Order Reminder - {order.order_number}',
            f'Your order {order.order_number} is still pending. Please complete your payment.',
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.email]
        )
        messages.append(message)
    
    if messages:
        send_mass_mail(messages, fail_silently=False)
    
    return f"Sent {len(messages)} order reminders"

@shared_task
def cleanup_sessions():
    """Clean up expired sessions."""
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    Session.objects.filter(expire_date__lt=timezone.now()).delete()
    
    return "Expired sessions cleaned up"

@shared_task
def generate_monthly_analytics():
    """Generate monthly analytics report."""
    from dateutil.relativedelta import relativedelta
    
    # Get last month's date range
    today = timezone.now().date()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    
    # Generate analytics
    analytics = {
        'period': f"{first_day_last_month} to {last_day_last_month}",
        'new_customers': Customer.objects.filter(
            created_at__date__range=[first_day_last_month, last_day_last_month]
        ).count(),
        'total_orders': Order.objects.filter(
            order_date__date__range=[first_day_last_month, last_day_last_month]
        ).count(),
        'total_revenue': Order.objects.filter(
            order_date__date__range=[first_day_last_month, last_day_last_month],
            status='delivered'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
    }
    
    # Store in database
    MonthlyAnalytics.objects.create(**analytics)
    
    # Generate and send report
    report = generate_analytics_report(analytics)
    send_mail(
        subject=f'Monthly Analytics - {analytics["period"]}',
        message='Monthly analytics report attached.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        attachments=[('monthly_analytics.pdf', report, 'application/pdf')]
    )
    
    return "Monthly analytics generated"

# 3. Task Monitoring
# admin.py
from django.contrib import admin
from django_celery_results.models import TaskResult

@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'task_name', 'status', 'date_done']
    list_filter = ['status', 'task_name', 'date_done']
    search_fields = ['task_id', 'task_name']
    readonly_fields = ['result', 'traceback']

# 4. Custom Task Status Page
# views.py
from celery.result import AsyncResult

def task_status(request, task_id):
    """Get task status and progress."""
    result = AsyncResult(task_id)
    
    response_data = {
        'task_id': task_id,
        'status': result.status,
        'result': result.result
    }
    
    # Include progress for long-running tasks
    if result.status == 'PROGRESS':
        response_data['current'] = result.info.get('current', 0)
        response_data['total'] = result.info.get('total', 1)
        response_data['percent'] = result.info.get('percent', 0)
    
    return JsonResponse(response_data)

# 5. Task Retry and Error Handling
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3}
)
def send_email_with_retry(self, to_email, subject, message):
    """Send email with automatic retry on failure."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False
        )
        return f"Email sent to {to_email}"
    except Exception as exc:
        # Log the error
        logger.error(f"Email sending failed: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)
```

### 13.10 Documentation Standards

```markdown
# Documentation Standards

## 1. Code Documentation

### Python Docstrings (Google Style)
```python
def calculate_customer_lifetime_value(customer_id: int, include_pending: bool = False) -> Decimal:
    """
    Calculate the lifetime value of a customer.
    
    This function calculates the total revenue generated by a customer
    throughout their relationship with the company.
    
    Args:
        customer_id: The unique identifier of the customer.
        include_pending: Whether to include pending orders in the calculation.
            Defaults to False.
    
    Returns:
        The total lifetime value as a Decimal.
        Returns Decimal('0') if the customer has no orders.
    
    Raises:
        Customer.DoesNotExist: If the customer with the given ID doesn't exist.
        ValueError: If customer_id is not a positive integer.
    
    Example:
        >>> ltv = calculate_customer_lifetime_value(123)
        >>> print(f"Customer LTV: ${ltv}")
        Customer LTV: $5420.50
    
    Note:
        This calculation includes only delivered orders by default.
        Use include_pending=True to include pending orders.
    """
    if not isinstance(customer_id, int) or customer_id <= 0:
        raise ValueError("customer_id must be a positive integer")
    
    customer = Customer.objects.get(pk=customer_id)
    
    filters = {'customer': customer}
    if not include_pending:
        filters['status'] = 'delivered'
    
    total = Order.objects.filter(**filters).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    return total
```

### JavaScript Documentation (JSDoc)
```javascript
/**
 * Initialize the customer data table with sorting and pagination.
 * 
 * @param {string} tableId - The ID of the table element
 * @param {Object} options - Configuration options
 * @param {number} options.pageSize - Number of rows per page (default: 25)
 * @param {boolean} options.responsive - Enable responsive mode (default: true)
 * @param {Array} options.columns - Column definitions
 * @returns {DataTable} The initialized DataTable instance
 * 
 * @example
 * const table = initializeDataTable('customer-table', {
 *     pageSize: 50,
 *     columns: [
 *         { data: 'name', title: 'Customer Name' },
 *         { data: 'email', title: 'Email Address' }
 *     ]
 * });
 */
function initializeDataTable(tableId, options = {}) {
    const defaults = {
        pageSize: 25,
        responsive: true,
        columns: []
    };
    
    const config = { ...defaults, ...options };
    
    return $(`#${tableId}`).DataTable({
        pageLength: config.pageSize,
        responsive: config.responsive,
        columns: config.columns,
        order: [[0, 'desc']],
        language: {
            search: getTranslation('search'),
            paginate: {
                first: getTranslation('first'),
                last: getTranslation('last'),
                next: getTranslation('next'),
                previous: getTranslation('previous')
            }
        }
    });
}
```

## 2. API Documentation

### REST API Endpoint Documentation
```yaml
# GET /api/v1/customers/
Description: Retrieve a paginated list of customers
Authentication: Required (Bearer Token)
Permissions: customers.view_customer

Query Parameters:
  - page: integer (optional)
    Description: Page number for pagination
    Default: 1
    Example: 2
    
  - page_size: integer (optional)
    Description: Number of items per page
    Default: 25
    Maximum: 100
    Example: 50
    
  - search: string (optional)
    Description: Search query for filtering customers
    Searches in: first_name, last_name, email, company_name
    Example: "john"
    
  - status: string (optional)
    Description: Filter by customer status
    Allowed values: lead, prospect, customer, inactive, archived
    Example: "customer"
    
  - ordering: string (optional)
    Description: Field to sort by (prefix with - for descending)
    Allowed fields: created_at, updated_at, first_name, last_name
    Default: "-created_at"
    Example: "last_name"

Response:
  Status: 200 OK
  Content-Type: application/json
  Schema:
    {
      "count": 150,
      "next": "http://api.example.com/api/v1/customers/?page=2",
      "previous": null,
      "results": [
        {
          "id": 1,
          "first_name": "John",
          "last_name": "Doe",
          "email": "john.doe@example.com",
          "phone": "+1234567890",
          "company_name": "ACME Corp",
          "status": "customer",
          "total_orders": 5,
          "total_spent": "2500.00",
          "created_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-03-20T14:45:00Z"
        }
      ]
    }

Error Responses:
  401 Unauthorized:
    {
      "detail": "Authentication credentials were not provided."
    }
    
  403 Forbidden:
    {
      "detail": "You do not have permission to perform this action."
    }

Example Request:
  curl -X GET "https://api.example.com/api/v1/customers/?search=john&status=customer" \
       -H "Authorization: Bearer your-token-here"
```

## 3. User Documentation

### Feature Documentation Template
```markdown
# Customer Management Module

## Overview
The Customer Management module allows you to manage your customer relationships effectively. This includes creating customer profiles, tracking interactions, and analyzing customer behavior.

## Features
- Customer CRUD operations
- Advanced search and filtering
- Customer activity tracking
- Excel import/export
- Email integration

## Getting Started

### Creating a New Customer
1. Navigate to the Customers page from the main menu
2. Click the "Yeni Müşteri" (New Customer) button
3. Fill in the required fields:
   - First Name (required)
   - Last Name (required)
   - Email (unique)
   - Phone Number
4. Click "Kaydet" (Save) to create the customer

### Searching for Customers
Use the search bar at the top of the customer list to find customers by:
- Name
- Email
- Company
- Phone number

### Filtering Customers
Apply filters to narrow down your customer list:
- Status (Lead, Prospect, Customer, etc.)
- Created Date Range
- Assigned User
- Location

## Advanced Features

### Bulk Import from Excel
1. Click "Excel ile İçe Aktar" (Import from Excel)
2. Download the template file
3. Fill in your customer data
4. Upload the completed file
5. Review and confirm the import

### Customer Analytics
View detailed analytics for each customer:
- Total orders
- Lifetime value
- Average order value
- Purchase frequency

## Best Practices
- Keep customer information up-to-date
- Use status fields to track customer lifecycle
- Add notes for important interactions
- Regularly export backups of your customer data

## Troubleshooting

### Common Issues

**Issue**: Cannot create customer with duplicate email
**Solution**: Each customer must have a unique email address. Check if the email already exists in the system.

**Issue**: Excel import fails
**Solution**: Ensure your Excel file matches the template format exactly. Check for:
- Correct column headers
- Valid data types
- No empty required fields

## Related Documentation
- [Order Management](./orders.md)
- [Product Catalog](./products.md)
- [Reporting](./reports.md)
```

## 4. README Template

### Project README
```markdown
# VivaCRM v2.0

Modern Customer Relationship Management system built with Django and HTMX.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Node.js 18+

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourorg/vivacrm-v2.git
   cd vivacrm-v2
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Load sample data (optional):
   ```bash
   python manage.py loaddata fixtures/sample_data.json
   ```

8. Run the development server:
   ```bash
   python manage.py runserver
   ```

## 🐳 Docker Setup

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Access the application at http://localhost:8000

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_customers.py
```

## 📚 Documentation

- [User Guide](docs/user-guide.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django Team for the amazing framework
- HTMX for making web apps interactive
- All contributors who have helped shape this project
```

## 5. Changelog Format

### CHANGELOG.md
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Excel bulk import for products
- Customer activity timeline
- Advanced search filters

### Changed
- Improved dashboard performance
- Updated to Django 5.0
- Redesigned customer detail page

### Fixed
- Fixed pagination issues on mobile devices
- Resolved date formatting in exports
- Corrected timezone handling

## [2.0.0] - 2024-01-15

### Added
- Complete UI redesign with TailwindCSS
- HTMX integration for dynamic updates
- Real-time notifications
- Multi-language support (Turkish/English)

### Changed
- Migrated from jQuery to Alpine.js
- Improved API response times by 40%
- Enhanced security with 2FA support

### Deprecated
- Legacy API endpoints (v1)
- Old jQuery plugins

### Removed
- Flash-based charts
- Deprecated user roles

### Fixed
- Memory leaks in report generation
- CSV export encoding issues

### Security
- Updated dependencies to patch CVE-2023-xxxxx
- Implemented rate limiting on API endpoints
```

## 6. Comments and Inline Documentation

### Good Comments
```python
# Calculate the weighted average of product ratings
# Weight is based on the number of reviews and recency
def calculate_weighted_rating(product):
    """
    Calculate weighted product rating.
    
    Recent reviews have more weight than older ones.
    Products with more reviews get a credibility boost.
    """
    # Get all reviews from the last 6 months
    recent_reviews = product.reviews.filter(
        created_at__gte=timezone.now() - timedelta(days=180)
    )
    
    if not recent_reviews.exists():
        return 0
    
    # Apply time-based weights (newer = higher weight)
    weighted_sum = 0
    weight_total = 0
    
    for review in recent_reviews:
        days_old = (timezone.now() - review.created_at).days
        # Weight decreases linearly over 180 days
        weight = 1 - (days_old / 180)
        
        weighted_sum += review.rating * weight
        weight_total += weight
    
    # Calculate base weighted average
    weighted_avg = weighted_sum / weight_total if weight_total > 0 else 0
    
    # Apply credibility boost based on number of reviews
    # More reviews = more reliable rating
    review_count = recent_reviews.count()
    credibility_factor = min(1, review_count / 10)  # Max boost at 10+ reviews
    
    # Final rating: 80% weighted average + 20% credibility boost
    final_rating = (weighted_avg * 0.8) + (5 * credibility_factor * 0.2)
    
    return round(final_rating, 1)
```

### Bad Comments (Avoid These)
```python
# DON'T DO THIS
def calc(p):
    # Calculate  
    r = p.reviews.filter(created_at__gte=timezone.now() - timedelta(days=180))
    if not r.exists():
        return 0
    # Do the math
    ws = 0
    wt = 0
    for review in r:
        d = (timezone.now() - review.created_at).days
        w = 1 - (d / 180)  # weight
        ws += review.rating * w
        wt += w
    wa = ws / wt if wt > 0 else 0
    rc = r.count()
    cf = min(1, rc / 10)
    fr = (wa * 0.8) + (5 * cf * 0.2)
    return round(fr, 1)
```
```

### 13.11 Migration Guide

```markdown
# VivaCRM v1.x to v2.0 Migration Guide

## Overview

This guide helps you migrate from VivaCRM v1.x to v2.0. The new version includes significant architectural changes, UI improvements, and new features.

## Major Changes

### 1. Frontend Architecture
- **Old**: jQuery + Bootstrap
- **New**: HTMX + Alpine.js + TailwindCSS

### 2. Database Changes
- New fields added to Customer model
- Order status workflow updated
- Product categories hierarchical structure

### 3. API Changes
- New RESTful API structure
- Authentication moved to token-based
- Pagination format changed

## Pre-Migration Checklist

- [ ] Backup your database
- [ ] Backup media files
- [ ] Note custom modifications
- [ ] Test in staging environment
- [ ] Plan downtime window
- [ ] Notify users

## Migration Steps

### Step 1: Backup

```bash
# Database backup
pg_dump vivacrm_db > backup_$(date +%Y%m%d).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Code backup
git tag pre-v2-migration
git push origin pre-v2-migration
```

### Step 2: Update Code

```bash
# Pull new version
git checkout main
git pull origin main

# Create migration branch
git checkout -b migration-v2
```

### Step 3: Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# JavaScript dependencies
npm install

# Build frontend assets
npm run build
```

### Step 4: Database Migrations

```python
# migrations/0001_v2_migration.py
from django.db import migrations, models

def migrate_customer_data(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    
    # Migrate old status values
    status_mapping = {
        'active': 'customer',
        'potential': 'prospect',
        'new': 'lead'
    }
    
    for customer in Customer.objects.all():
        if customer.status in status_mapping:
            customer.status = status_mapping[customer.status]
            customer.save()

class Migration(migrations.Migration):
    dependencies = [
        ('customers', '0010_auto_20231201_1234'),
    ]
    
    operations = [
        # Add new fields
        migrations.AddField(
            model_name='customer',
            name='source',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='assigned_to',
            field=models.ForeignKey(
                'auth.User',
                on_delete=models.SET_NULL,
                null=True,
                related_name='assigned_customers'
            ),
        ),
        
        # Run data migration
        migrations.RunPython(migrate_customer_data),
    ]
```

### Step 5: Run Migrations

```bash
# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Step 6: Static Files

```bash
# Collect static files
python manage.py collectstatic --noinput

# Build Tailwind CSS
npm run build:css
```

### Step 7: Update Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... existing apps ...
    'crispy_forms',
    'crispy_tailwind',
    'django_htmx',
]

# Remove old middleware
MIDDLEWARE = [
    # Remove: 'old.middleware.CustomMiddleware',
    # Add:
    'django_htmx.middleware.HtmxMiddleware',
]

# Update templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # New template structure
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # ... existing ...
                'django.template.context_processors.static',
            ],
        },
    },
]
```

### Step 8: Data Verification

```python
# verification/check_migration.py
from django.core.management.base import BaseCommand
from customers.models import Customer
from orders.models import Order

class Command(BaseCommand):
    help = 'Verify data migration'
    
    def handle(self, *args, **options):
        # Check customer statuses
        invalid_statuses = Customer.objects.exclude(
            status__in=['lead', 'prospect', 'customer', 'inactive', 'archived']
        ).count()
        
        if invalid_statuses > 0:
            self.stdout.write(
                self.style.ERROR(f'{invalid_statuses} customers with invalid status')
            )
        
        # Check order references
        orphaned_orders = Order.objects.filter(customer__isnull=True).count()
        
        if orphaned_orders > 0:
            self.stdout.write(
                self.style.ERROR(f'{orphaned_orders} orders without customers')
            )
        
        self.stdout.write(self.style.SUCCESS('Migration verification complete'))
```

### Step 9: Update Integrations

```python
# Update API clients
# old_client.py
class OldAPIClient:
    def get_customers(self):
        response = requests.get(f'{self.base_url}/customers/')
        return response.json()  # Returns array

# new_client.py
class NewAPIClient:
    def get_customers(self, page=1):
        response = requests.get(
            f'{self.base_url}/api/v1/customers/',
            params={'page': page}
        )
        data = response.json()
        return data['results']  # Paginated response
```

### Step 10: Test

```bash
# Run test suite
pytest

# Manual testing checklist
- [ ] User authentication
- [ ] Customer CRUD operations
- [ ] Order creation
- [ ] Report generation
- [ ] Email notifications
- [ ] File uploads
```

## Post-Migration Tasks

### 1. Monitor Performance

```python
# monitoring/check_performance.py
import time
from django.test import Client

def check_response_times():
    client = Client()
    endpoints = [
        '/customers/',
        '/orders/',
        '/products/',
        '/api/v1/customers/',
    ]
    
    for endpoint in endpoints:
        start = time.time()
        response = client.get(endpoint)
        duration = time.time() - start
        
        if duration > 1.0:  # Slow response
            print(f"SLOW: {endpoint} took {duration:.2f}s")
        else:
            print(f"OK: {endpoint} took {duration:.2f}s")
```

### 2. Update Documentation

- Update API documentation
- Update user guides
- Update deployment procedures
- Train users on new features

### 3. Clean Up

```bash
# Remove old code
git rm -r legacy/

# Remove unused dependencies
pip uninstall old-package

# Clean up media files
python manage.py cleanup_unused_media
```

## Rollback Plan

If issues occur during migration:

```bash
# Rollback database
psql vivacrm_db < backup_20240115.sql

# Rollback code
git checkout v1.x-stable
git cherry-pick <hotfix-commits>

# Restore media
tar -xzf media_backup_20240115.tar.gz
```

## Common Issues and Solutions

### Issue 1: Template Errors
**Problem**: Old templates using Bootstrap classes
**Solution**: Update templates to use TailwindCSS classes

```html
<!-- Old -->
<div class="col-md-6">
    <div class="card">
        <div class="card-body">
            Content
        </div>
    </div>
</div>

<!-- New -->
<div class="w-full md:w-1/2">
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
            Content
        </div>
    </div>
</div>
```

### Issue 2: JavaScript Errors
**Problem**: jQuery code not working
**Solution**: Rewrite using Alpine.js or vanilla JavaScript

```javascript
// Old (jQuery)
$('#submit-btn').click(function() {
    var data = $('#form').serialize();
    $.post('/api/submit/', data, function(response) {
        $('#result').html(response.message);
    });
});

// New (Alpine.js + HTMX)
<button 
    @click="submitForm"
    hx-post="/api/submit/"
    hx-trigger="click"
    hx-target="#result"
    class="btn btn-primary"
>
    Submit
</button>
```

### Issue 3: API Authentication
**Problem**: Old session-based auth not working
**Solution**: Update to token-based authentication

```python
# Old
def api_view(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

# New
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_view(request):
    # Automatically handles authentication
    pass
```

## Support

For migration support:
- Check the [Migration FAQ](https://docs.vivacrm.com/migration-faq)
- Join our [Slack channel](https://vivacrm.slack.com)
- Email: support@vivacrm.com
```

### 13.12 Development Environment Configuration

```python
# Development Environment Configuration

# 1. Local Settings Override
# settings/local.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.ngrok.io']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vivacrm_dev',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Email (Development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']

# Celery (Development)
CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True

# Static files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# 2. Docker Development Environment
# docker-compose.dev.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: vivacrm_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP server
      - "8025:8025"  # Web UI
  
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/vivacrm_dev
      - REDIS_URL=redis://redis:6379/1
      - DEBUG=True
  
  celery:
    build: .
    command: celery -A core worker -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/vivacrm_dev
      - REDIS_URL=redis://redis:6379/1
  
  celery-beat:
    build: .
    command: celery -A core beat -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/vivacrm_dev
      - REDIS_URL=redis://redis:6379/1

volumes:
  postgres_data:

# 3. VS Code Configuration
# .vscode/settings.json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        ".coverage": true,
        "htmlcov": true
    },
    "emmet.includeLanguages": {
        "django-html": "html"
    },
    "[django-html]": {
        "editor.defaultFormatter": "batisteo.vscode-django"
    }
}

# .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": [
                "runserver"
            ],
            "django": true,
            "env": {
                "DJANGO_SETTINGS_MODULE": "core.settings.local"
            }
        },
        {
            "name": "Django Shell",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": [
                "shell_plus"
            ],
            "django": true
        },
        {
            "name": "Celery Worker",
            "type": "python",
            "request": "launch",
            "module": "celery",
            "args": [
                "-A",
                "core",
                "worker",
                "-l",
                "info"
            ]
        },
        {
            "name": "Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "-v"
            ]
        }
    ]
}

# 4. Pre-commit Hooks
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203,W503']
        
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile', 'black']
        
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      
  - repo: https://github.com/pycqa/pylint
    rev: v3.0.0
    hooks:
      - id: pylint
        args: ['--disable=C0103,C0111,R0903,W0212']

# 5. Environment Variables Template
# .env.example
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vivacrm_dev

# Redis
REDIS_URL=redis://localhost:6379/1

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@vivacrm.local

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AWS (Optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Sentry (Optional)
SENTRY_DSN=

# Google Maps API (Optional)
GOOGLE_MAPS_API_KEY=

# 6. Makefile for Common Tasks
# Makefile
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make migrate    - Run database migrations"
	@echo "  make test       - Run tests"
	@echo "  make coverage   - Run tests with coverage"
	@echo "  make lint       - Run linting"
	@echo "  make format     - Format code"
	@echo "  make shell      - Open Django shell"
	@echo "  make server     - Run development server"
	@echo "  make celery     - Run Celery worker"
	@echo "  make beat       - Run Celery beat"
	@echo "  make docker-up  - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"

install:
	pip install -r requirements.txt
	npm install
	pre-commit install

migrate:
	python manage.py migrate

test:
	pytest

coverage:
	pytest --cov=. --cov-report=html
	open htmlcov/index.html

lint:
	flake8 .
	pylint **/*.py

format:
	black .
	isort .

shell:
	python manage.py shell_plus

server:
	python manage.py runserver

celery:
	celery -A core worker -l info

beat:
	celery -A core beat -l info

docker-up:
	docker-compose -f docker-compose.dev.yml up

docker-down:
	docker-compose -f docker-compose.dev.yml down

# 7. Sample Data Generator
# management/commands/generate_sample_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
from customers.models import Customer
from products.models import Product, ProductCategory
from orders.models import Order, OrderItem

fake = Faker('tr_TR')  # Turkish locale

class Command(BaseCommand):
    help = 'Generate sample data for development'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--customers',
            type=int,
            default=100,
            help='Number of customers to create'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=50,
            help='Number of products to create'
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=200,
            help='Number of orders to create'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Generating sample data...')
        
        # Create categories
        categories = []
        for cat_name in ['Elektronik', 'Giyim', 'Kitap', 'Oyuncak', 'Spor']:
            category, _ = ProductCategory.objects.get_or_create(name=cat_name)
            categories.append(category)
        
        # Create products
        products = []
        for i in range(options['products']):
            product = Product.objects.create(
                name=fake.catch_phrase(),
                sku=f'SKU-{i:04d}',
                description=fake.text(),
                price=random.uniform(10, 1000),
                cost=random.uniform(5, 500),
                stock_quantity=random.randint(0, 100),
                category=random.choice(categories),
                status='active'
            )
            products.append(product)
        
        # Create customers
        customers = []
        for i in range(options['customers']):
            customer = Customer.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number(),
                company_name=fake.company(),
                address=fake.address(),
                city=fake.city(),
                country='Türkiye',
                status=random.choice(['lead', 'prospect', 'customer']),
                created_at=fake.date_time_this_year(tzinfo=timezone.utc)
            )
            customers.append(customer)
        
        # Create orders
        for i in range(options['orders']):
            customer = random.choice(customers)
            order = Order.objects.create(
                customer=customer,
                status=random.choice(['pending', 'processing', 'shipped', 'delivered']),
                payment_status=random.choice(['pending', 'paid']),
                shipping_address=customer.address,
                shipping_city=customer.city,
                shipping_country=customer.country,
                billing_address=customer.address,
                billing_city=customer.city,
                billing_country=customer.country,
                order_date=fake.date_time_this_year(tzinfo=timezone.utc)
            )
            
            # Add order items
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                product = random.choice(products)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 5),
                    unit_price=product.price
                )
            
            order.calculate_total()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {options["customers"]} customers, '
                f'{options["products"]} products, and {options["orders"]} orders'
            )
        )
```

### 13.13 Continuous Integration/Continuous Deployment

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: vivacrm_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest-cov
    
    - name: Run migrations
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/vivacrm_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        python manage.py migrate
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/vivacrm_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Run linting
      run: |
        flake8 .
        black --check .
        isort --check-only .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
        DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
      run: |
        echo "$DEPLOY_KEY" > deploy_key
        chmod 600 deploy_key
        ssh -i deploy_key -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST 'cd /app && git pull && docker-compose up -d'

# .github/workflows/codeql.yml
name: "CodeQL"

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '30 1 * * 1'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python', 'javascript' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
```

### 13.14 Monitoring and Logging Production

```python
# Production Monitoring and Logging

# 1. Structured Logging
# settings/production.py
import structlog

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json_formatter': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json_formatter',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/vivacrm/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json_formatter',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'vivacrm': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# 2. Application Performance Monitoring (APM)
# utils/monitoring.py
import time
from functools import wraps
from django.core.cache import cache
import structlog

logger = structlog.get_logger()

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log performance metrics
            logger.info(
                "function_executed",
                function=func.__name__,
                module=func.__module__,
                duration=duration,
                args=str(args)[:100],  # Truncate for security
                success=True
            )
            
            # Store metrics in cache for dashboard
            cache_key = f"metrics:{func.__module__}.{func.__name__}"
            metrics = cache.get(cache_key, {
                'count': 0,
                'total_duration': 0,
                'errors': 0
            })
            
            metrics['count'] += 1
            metrics['total_duration'] += duration
            
            cache.set(cache_key, metrics, 3600)  # 1 hour
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "function_error",
                function=func.__name__,
                module=func.__module__,
                duration=duration,
                error=str(e),
                args=str(args)[:100]
            )
            
            # Update error metrics
            cache_key = f"metrics:{func.__module__}.{func.__name__}"
            metrics = cache.get(cache_key, {
                'count': 0,
                'total_duration': 0,
                'errors': 0
            })
            
            metrics['errors'] += 1
            cache.set(cache_key, metrics, 3600)
            
            raise
    
    return wrapper

# 3. Custom Middleware for Request Monitoring
# middleware/monitoring.py
import uuid
import time
from django.utils.deprecation import MiddlewareMixin
import structlog

logger = structlog.get_logger()

class RequestMonitoringMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Log request start
        logger.info(
            "request_started",
            request_id=request.id,
            method=request.method,
            path=request.path,
            user=getattr(request.user, 'username', 'anonymous'),
            ip=self.get_client_ip(request)
        )
        
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log request completion
            logger.info(
                "request_completed",
                request_id=getattr(request, 'id', 'unknown'),
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration=duration,
                user=getattr(request.user, 'username', 'anonymous')
            )
        
        return response
    
    def process_exception(self, request, exception):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log request error
            logger.error(
                "request_error",
                request_id=getattr(request, 'id', 'unknown'),
                method=request.method,
                path=request.path,
                error=str(exception),
                duration=duration,
                user=getattr(request.user, 'username', 'anonymous')
            )
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# 4. Health Check Endpoint
# views/monitoring.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from celery import current_app

def health_check(request):
    """Comprehensive health check endpoint."""
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error: cannot read from cache'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Redis check
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status['checks']['redis'] = 'ok'
    except Exception as e:
        health_status['checks']['redis'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Celery check
    try:
        celery_status = current_app.control.inspect().stats()
        if celery_status:
            health_status['checks']['celery'] = 'ok'
        else:
            health_status['checks']['celery'] = 'error: no workers available'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['celery'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)

# 5. Metrics Dashboard
# views/metrics.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db import connection
import psutil

@staff_member_required
def metrics_dashboard(request):
    """Display system metrics dashboard."""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database metrics
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity
        """)
        db_metrics = cursor.fetchone()
    
    # Application metrics
    app_metrics = {
        'total_customers': Customer.objects.count(),
        'active_orders': Order.objects.filter(status='processing').count(),
        'low_stock_products': Product.objects.filter(
            stock_quantity__lte=F('low_stock_threshold')
        ).count(),
    }
    
    # Cache metrics
    cache_keys = cache.keys('metrics:*')
    function_metrics = []
    
    for key in cache_keys:
        metrics = cache.get(key)
        if metrics:
            function_name = key.replace('metrics:', '')
            avg_duration = metrics['total_duration'] / metrics['count'] if metrics['count'] > 0 else 0
            error_rate = metrics['errors'] / metrics['count'] * 100 if metrics['count'] > 0 else 0
            
            function_metrics.append({
                'name': function_name,
                'count': metrics['count'],
                'avg_duration': avg_duration,
                'error_rate': error_rate
            })
    
    context = {
        'system_metrics': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory.used // (1024 * 1024),  # MB
            'memory_total': memory.total // (1024 * 1024),  # MB
            'disk_percent': disk.percent,
            'disk_used': disk.used // (1024 * 1024 * 1024),  # GB
            'disk_total': disk.total // (1024 * 1024 * 1024),  # GB
        },
        'db_metrics': {
            'total_connections': db_metrics[0],
            'active_connections': db_metrics[1],
            'idle_connections': db_metrics[2],
        },
        'app_metrics': app_metrics,
        'function_metrics': sorted(function_metrics, key=lambda x: x['count'], reverse=True)[:20],
    }
    
    return render(request, 'monitoring/metrics_dashboard.html', context)

# 6. Error Tracking with Sentry
# settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(
            transaction_style='url',
            middleware_spans=True,
            signals_spans=True,
            cache_spans=True,
        ),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    send_default_pii=False,  # Don't send personally identifiable information
    environment=os.environ.get('ENVIRONMENT', 'production'),
    release=os.environ.get('GIT_COMMIT', 'unknown'),
    before_send=lambda event, hint: sanitize_sentry_event(event, hint),
)

def sanitize_sentry_event(event, hint):
    """Remove sensitive data from Sentry events."""
    if 'request' in event:
        request = event['request']
        
        # Remove sensitive headers
        if 'headers' in request:
            sensitive_headers = ['Authorization', 'Cookie', 'X-CSRFToken']
            for header in sensitive_headers:
                if header in request['headers']:
                    request['headers'][header] = '[REDACTED]'
        
        # Remove sensitive data from request data
        if 'data' in request:
            sensitive_fields = ['password', 'credit_card', 'ssn']
            for field in sensitive_fields:
                if field in request['data']:
                    request['data'][field] = '[REDACTED]'
    
    return event

# 7. Performance Optimization Monitoring
# management/commands/analyze_performance.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
import time

class Command(BaseCommand):
    help = 'Analyze application performance'
    
    def handle(self, *args, **options):
        self.stdout.write('Analyzing application performance...')
        
        # Analyze slow queries
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    mean_time,
                    total_time
                FROM pg_stat_statements
                WHERE mean_time > 100  -- Queries taking more than 100ms
                ORDER BY mean_time DESC
                LIMIT 20
            """)
            
            slow_queries = cursor.fetchall()
            
            self.stdout.write('\nSlow Queries:')
            for query in slow_queries:
                self.stdout.write(f"Query: {query[0][:50]}...")
                self.stdout.write(f"Calls: {query[1]}, Avg Time: {query[2]:.2f}ms")
        
        # Analyze cache hit rates
        cache_stats = cache.get_stats()
        if cache_stats:
            hit_rate = cache_stats.get('hits', 0) / (cache_stats.get('hits', 0) + cache_stats.get('misses', 1)) * 100
            self.stdout.write(f'\nCache Hit Rate: {hit_rate:.2f}%')
        
        # Analyze endpoint performance
        function_metrics = []
        cache_keys = cache.keys('metrics:*')
        
        for key in cache_keys:
            metrics = cache.get(key)
            if metrics and metrics['count'] > 0:
                avg_duration = metrics['total_duration'] / metrics['count']
                function_metrics.append({
                    'name': key.replace('metrics:', ''),
                    'avg_duration': avg_duration,
                    'count': metrics['count']
                })
        
        self.stdout.write('\nSlowest Endpoints:')
        for metric in sorted(function_metrics, key=lambda x: x['avg_duration'], reverse=True)[:10]:
            self.stdout.write(f"{metric['name']}: {metric['avg_duration']:.3f}s (called {metric['count']} times)")
```

### 13.15 Final Checklist and Best Practices

```markdown
# VivaCRM Development Final Checklist

## Pre-Development Checklist

### Environment Setup
- [ ] Python 3.11+ installed
- [ ] PostgreSQL 13+ running
- [ ] Redis 6+ available
- [ ] Node.js 18+ installed
- [ ] Virtual environment created
- [ ] Environment variables configured
- [ ] Pre-commit hooks installed

### Code Quality Tools
- [ ] Black formatter configured
- [ ] Flake8 linter set up
- [ ] isort import sorter configured
- [ ] pytest testing framework ready
- [ ] Coverage.py installed

## Development Checklist

### Backend Development
- [ ] Models follow naming conventions
- [ ] All models have `__str__` methods
- [ ] Database indexes added where needed
- [ ] Migrations are reversible
- [ ] Views handle errors gracefully
- [ ] Permissions checked in views
- [ ] Forms have proper validation
- [ ] API endpoints documented
- [ ] Celery tasks are idempotent
- [ ] Background tasks have retry logic

### Frontend Development
- [ ] Templates use proper inheritance
- [ ] HTMX patterns implemented correctly
- [ ] Alpine.js components are reactive
- [ ] TailwindCSS classes organized
- [ ] JavaScript code is modular
- [ ] Forms have client-side validation
- [ ] Loading states implemented
- [ ] Error messages are user-friendly
- [ ] Responsive design tested
- [ ] Accessibility features included

### Testing
- [ ] Unit tests for all models
- [ ] View tests for all endpoints
- [ ] API tests for all routes
- [ ] Form validation tests
- [ ] JavaScript function tests
- [ ] E2E tests for critical paths
- [ ] Test coverage > 80%
- [ ] Performance tests for slow queries

### Security
- [ ] CSRF protection enabled
- [ ] XSS prevention implemented
- [ ] SQL injection prevented
- [ ] File upload validation
- [ ] Password policies enforced
- [ ] Rate limiting configured
- [ ] Sensitive data encrypted
- [ ] Security headers set

### Documentation
- [ ] Code comments added
- [ ] Docstrings written
- [ ] API documentation updated
- [ ] User guide current
- [ ] README.md complete
- [ ] CHANGELOG.md updated
- [ ] Migration guide prepared
- [ ] Architecture diagram current

## Pre-Deployment Checklist

### Code Review
- [ ] All PRs reviewed
- [ ] Code style consistent
- [ ] No console.log statements
- [ ] No debugging code
- [ ] No hardcoded values
- [ ] No TODO comments
- [ ] No deprecated functions
- [ ] Dependencies up to date

### Performance
- [ ] Database queries optimized
- [ ] N+1 queries eliminated
- [ ] Caching implemented
- [ ] Static files minified
- [ ] Images optimized
- [ ] CDN configured
- [ ] Compression enabled
- [ ] Load testing completed

### Configuration
- [ ] Production settings separate
- [ ] Secret keys rotated
- [ ] Debug mode disabled
- [ ] Allowed hosts configured
- [ ] SSL certificates ready
- [ ] Backup strategy defined
- [ ] Monitoring tools set up
- [ ] Error tracking configured

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Database backup taken
- [ ] Media files backed up
- [ ] Deployment notes prepared
- [ ] Rollback plan ready
- [ ] Team notified
- [ ] Maintenance window scheduled
- [ ] Dependencies frozen

### Deployment Process
- [ ] Code deployed to staging
- [ ] Staging tests completed
- [ ] Database migrations run
- [ ] Static files collected
- [ ] Services restarted
- [ ] Health checks passing
- [ ] Smoke tests completed
- [ ] Performance monitored

### Post-Deployment
- [ ] Error logs checked
- [ ] Performance metrics reviewed
- [ ] User feedback collected
- [ ] Documentation updated
- [ ] Lessons learned documented
- [ ] Next sprint planned
- [ ] Technical debt logged
- [ ] Success celebrated! 🎉

## Best Practices Summary

### Code Quality
1. **Follow PEP 8** for Python code
2. **Use type hints** where beneficial
3. **Write self-documenting code**
4. **Keep functions small and focused**
5. **Avoid deep nesting** (max 3 levels)
6. **Use meaningful variable names**
7. **Comment complex logic only**
8. **Refactor duplicated code**

### Database
1. **Use select_related()** for ForeignKeys
2. **Use prefetch_related()** for ManyToMany
3. **Add database indexes** strategically
4. **Use bulk operations** when possible
5. **Implement soft deletes** where needed
6. **Version control migrations**
7. **Test migrations** before deployment
8. **Monitor query performance**

### Security
1. **Never trust user input**
2. **Use parameterized queries**
3. **Implement least privilege**
4. **Encrypt sensitive data**
5. **Use secure password hashing**
6. **Implement rate limiting**
7. **Log security events**
8. **Regular security audits**

### Frontend
1. **Progressive enhancement** approach
2. **Mobile-first design**
3. **Optimize for performance**
4. **Implement lazy loading**
5. **Use semantic HTML**
6. **Follow accessibility guidelines**
7. **Test across browsers**
8. **Minimize JavaScript**

### Testing
1. **Write tests first** (TDD)
2. **Test edge cases**
3. **Mock external services**
4. **Keep tests independent**
5. **Use descriptive test names**
6. **Maintain test fixtures**
7. **Run tests before commit**
8. **Monitor test coverage**

### Documentation
1. **Document as you code**
2. **Keep README updated**
3. **Use clear examples**
4. **Explain "why" not just "what"**
5. **Include troubleshooting**
6. **Version documentation**
7. **Use diagrams when helpful**
8. **Review documentation regularly**

### Team Collaboration
1. **Use meaningful commit messages**
2. **Create focused pull requests**
3. **Review code constructively**
4. **Share knowledge sessions**
5. **Document decisions**
6. **Communicate blockers early**
7. **Celebrate successes**
8. **Learn from failures**

## Resources

### Official Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [HTMX Documentation](https://htmx.org/docs/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)

### Community Resources
- [Django Forum](https://forum.djangoproject.com/)
- [Python Discord](https://discord.gg/python)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/django)

### Learning Resources
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [HTMX Examples](https://htmx.org/examples/)
- [Alpine.js Tutorials](https://alpinejs.dev/tutorials)

---

Built with ❤️ by the VivaCRM Team
```

---

## Conclusion

This comprehensive development documentation for VivaCRM v2.0 covers all aspects of the system from architecture to deployment. The document serves as both a reference guide and a learning resource for developers working on the project.

Key highlights:
- Modern Django architecture with HTMX and Alpine.js
- Comprehensive testing strategy
- Security best practices
- Performance optimization techniques
- Detailed deployment procedures
- Extensive code examples
- Clear documentation standards

The combination of Django's robustness with modern frontend technologies creates a powerful, maintainable, and scalable CRM solution that meets contemporary web application standards while maintaining simplicity and developer productivity.

For questions or contributions, please refer to the project repository or contact the development team.