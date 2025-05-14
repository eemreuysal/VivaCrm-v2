from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.edit import FormMixin, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, F, Sum
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator

from .models import (
    Category, Product, ProductImage, ProductAttribute, 
    ProductAttributeValue, StockMovement
)
from .forms import (
    CategoryForm, ProductForm, ProductImageForm, 
    ProductAttributeForm, ProductAttributeValueForm, ProductSearchForm,
    StockMovementForm, BulkStockAdjustmentForm
)


# Category Views
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'


class CategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_message = _("Kategori başarıyla oluşturuldu.")


class CategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_message = _("Kategori başarıyla güncellendi.")


class CategoryDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Category
    template_name = 'products/category_confirm_delete.html'
    success_url = reverse_lazy('products:category-list')
    success_message = _("Kategori başarıyla silindi.")


# Product Views
class ProductListView(LoginRequiredMixin, FormMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    form_class = ProductSearchForm
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form = self.get_form()
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            category = form.cleaned_data.get('category')
            status = form.cleaned_data.get('status')
            in_stock = form.cleaned_data.get('in_stock')
            low_stock = form.cleaned_data.get('low_stock')
            
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) | 
                    Q(code__icontains=query) | 
                    Q(sku__icontains=query) | 
                    Q(barcode__icontains=query)
                )
            
            if category:
                queryset = queryset.filter(category=category)
                
            if status:
                queryset = queryset.filter(status=status)
                
            if in_stock:
                queryset = queryset.filter(stock__gt=0)
                
            if low_stock:
                queryset = queryset.filter(is_physical=True, stock__gt=0, stock__lte=10)
        
        return queryset
    
    def get_initial(self):
        return {
            'query': self.request.GET.get('query', ''),
            'category': self.request.GET.get('category', ''),
            'status': self.request.GET.get('status', ''),
            'in_stock': self.request.GET.get('in_stock', False),
            'low_stock': self.request.GET.get('low_stock', False),
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add stock status information to the context
        context['low_stock_count'] = Product.objects.filter(
            is_physical=True, stock__gt=0, stock__lte=10
        ).count()
        context['out_of_stock_count'] = Product.objects.filter(
            is_physical=True, stock=0
        ).count()
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['image_form'] = ProductImageForm()
        context['attribute_value_form'] = ProductAttributeValueForm(product=self.object)
        
        # Add stock movement information
        context['stock_movements'] = self.object.stock_movements.all()[:10]
        context['stock_movement_form'] = StockMovementForm(initial={'product': self.object})
        
        # Add sales history (if there are any OrderItems)
        try:
            from orders.models import OrderItem
            context['sales_history'] = OrderItem.objects.filter(
                product=self.object, 
                order__status__in=['completed', 'delivered']
            ).order_by('-order__order_date')[:10]
        except:
            pass
            
        return context


class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_message = _("Ürün başarıyla oluşturuldu.")


class ProductUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_message = _("Ürün başarıyla güncellendi.")


class ProductDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:product-list')
    success_message = _("Ürün başarıyla silindi.")


# Product Image Views
class ProductImageCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProductImage
    form_class = ProductImageForm
    template_name = 'products/product_image_form.html'
    success_message = _("Ürün görseli başarıyla eklendi.")
    
    def form_valid(self, form):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        form.instance.product = product
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.kwargs['slug']})


class ProductImageDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductImage
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        product_slug = image.product.slug
        image.delete()
        return JsonResponse({
            'success': True,
            'message': _("Ürün görseli başarıyla silindi.")
        })
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# Product Attribute Views
class ProductAttributeListView(LoginRequiredMixin, ListView):
    model = ProductAttribute
    template_name = 'products/attribute_list.html'
    context_object_name = 'attributes'


class ProductAttributeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProductAttribute
    form_class = ProductAttributeForm
    template_name = 'products/attribute_form.html'
    success_url = reverse_lazy('products:attribute-list')
    success_message = _("Ürün özelliği başarıyla oluşturuldu.")


class ProductAttributeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProductAttribute
    form_class = ProductAttributeForm
    template_name = 'products/attribute_form.html'
    success_url = reverse_lazy('products:attribute-list')
    success_message = _("Ürün özelliği başarıyla güncellendi.")


class ProductAttributeDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ProductAttribute
    template_name = 'products/attribute_confirm_delete.html'
    success_url = reverse_lazy('products:attribute-list')
    success_message = _("Ürün özelliği başarıyla silindi.")


# Product Attribute Value Views
class ProductAttributeValueCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProductAttributeValue
    form_class = ProductAttributeValueForm
    template_name = 'products/attribute_value_form.html'
    success_message = _("Ürün özellik değeri başarıyla eklendi.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        kwargs['product'] = product
        return kwargs
    
    def form_valid(self, form):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        form.instance.product = product
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.kwargs['slug']})


class ProductAttributeValueUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProductAttributeValue
    fields = ['value']
    template_name = 'products/attribute_value_form.html'
    success_message = _("Ürün özellik değeri başarıyla güncellendi.")
    
    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.object.product.slug})


class ProductAttributeValueDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductAttributeValue
    
    def delete(self, request, *args, **kwargs):
        value = self.get_object()
        product_slug = value.product.slug
        value.delete()
        return JsonResponse({
            'success': True,
            'message': _("Ürün özellik değeri başarıyla silindi.")
        })
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# Stock Movement Views
class StockMovementListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = 'products/stock_movement_list.html'
    context_object_name = 'movements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by product if specified
        product_id = self.request.GET.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        # Filter by movement type if specified
        movement_type = self.request.GET.get('type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
            
        # Filter by date range if specified
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics
        context['total_movements'] = self.get_queryset().count()
        
        # Add filter parameters to context
        context['product_id'] = self.request.GET.get('product', '')
        context['movement_type'] = self.request.GET.get('type', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        
        # Add product list for filtering
        context['products'] = Product.objects.filter(is_active=True, is_physical=True)
        context['movement_types'] = dict(StockMovement.MOVEMENT_TYPE_CHOICES)
        
        return context


class StockMovementCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'products/stock_movement_form.html'
    success_message = _("Stok hareketi başarıyla kaydedildi.")
    success_url = reverse_lazy('products:movement-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        product_id = self.request.GET.get('product')
        if product_id:
            initial['product'] = product_id
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.request.GET.get('product')
        if product_id:
            try:
                context['product'] = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                pass
        return context


class StockMovementDetailView(LoginRequiredMixin, DetailView):
    model = StockMovement
    template_name = 'products/stock_movement_detail.html'
    context_object_name = 'movement'


def movement_fields_view(request):
    """
    Returns the appropriate fields based on movement type.
    Used with HTMX for dynamic form fields.
    """
    movement_type = request.GET.get('movement_type', '')
    context = {'movement_type': movement_type}
    
    # Different templates based on movement type
    if movement_type == 'purchase':
        return HttpResponse("""
            <div class="alert alert-info">
                <strong>Satın Alma:</strong> Yeni ürün alımları için kullanılır. Birim maliyet girilebilir.
            </div>
        """)
    elif movement_type == 'sale':
        return HttpResponse("""
            <div class="alert alert-warning">
                <strong>Satış:</strong> Manuel satış kaydı için kullanılır. Genellikle sipariş sistemi üzerinden otomatik olarak kaydedilir.
            </div>
        """)
    elif movement_type == 'return':
        return HttpResponse("""
            <div class="alert alert-success">
                <strong>İade:</strong> Müşteriden gelen iade ürünleri için kullanılır.
            </div>
        """)
    elif movement_type == 'adjustment':
        return HttpResponse("""
            <div class="alert alert-primary">
                <strong>Stok Düzeltme:</strong> Envanter sayımları sonrası düzeltmeler için kullanılır.
            </div>
        """)
    elif movement_type == 'waste':
        return HttpResponse("""
            <div class="alert alert-danger">
                <strong>Fire:</strong> Hasar görmüş, kullanılamaz durumdaki ürünlerin stoktan düşülmesi için kullanılır.
            </div>
        """)
    
    return HttpResponse()


class BulkStockAdjustmentView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'products/bulk_stock_adjustment.html'
    form_class = BulkStockAdjustmentForm
    success_url = reverse_lazy('products:product-list')
    success_message = _("Toplu stok ayarlaması başarıyla tamamlandı.")
    
    def form_valid(self, form):
        products = form.cleaned_data['products']
        adjustment_type = form.cleaned_data['adjustment_type']
        quantity = form.cleaned_data['quantity']
        notes = form.cleaned_data['notes'] or _("Toplu stok ayarlaması")
        
        for product in products:
            if adjustment_type == 'absolute':
                # Set stock to the exact value
                new_quantity = quantity
                movement_type = 'inventory'
                movement_quantity = quantity - product.stock  # Can be negative
            elif adjustment_type == 'increase':
                # Increase stock by the given amount
                movement_type = 'adjustment'
                movement_quantity = quantity
                new_quantity = product.stock + quantity
            else:  # decrease
                # Decrease stock by the given amount
                movement_type = 'waste'
                movement_quantity = min(quantity, product.stock)  # Can't go below 0
                new_quantity = max(0, product.stock - quantity)
            
            # Create stock movement
            if movement_quantity != 0:  # Only create movement if there's an actual change
                StockMovement.objects.create(
                    product=product,
                    movement_type=movement_type,
                    quantity=movement_quantity,
                    notes=notes,
                    created_by=self.request.user
                )
        
        return super().form_valid(form)