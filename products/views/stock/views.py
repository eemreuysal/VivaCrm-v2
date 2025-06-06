"""
Stock management views for products app.
"""
from django.views.generic import ListView, DetailView, CreateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required

from products.models import Product, StockMovement
from products.forms.stock import StockMovementForm, BulkStockAdjustmentForm


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


class BulkStockAdjustmentView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    """
    Bulk stock adjustment view.
    
    This view serves two purposes:
    1. As a UI for bulk stock adjustments
    2. As a temporary replacement for the stock-adjustment-import view
       (until the Excel importer for stock adjustments is implemented)
    """
    template_name = 'products/bulk_stock_adjustment.html'
    form_class = BulkStockAdjustmentForm
    success_url = reverse_lazy('products:product-list')
    success_message = _("Toplu stok ayarlaması başarıyla tamamlandı.")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # If accessed through the stock-adjustment-import URL, add a message about Excel import being under development
        if self.request.resolver_match.url_name == 'stock-adjustment-import':
            context['import_message'] = _("Excel ile toplu stok yükleme özelliği geliştirme aşamasındadır. "
                                        "Şimdilik manuel stok ayarlama aracını kullanabilirsiniz.")
            context['is_import_view'] = True
            context['page_title'] = _("Toplu Stok Yükleme")
        else:
            context['page_title'] = _("Toplu Stok Ayarlama")
        
        return context
    
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


@login_required
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