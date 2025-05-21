"""
Category views for products app.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta

from products.models import Category, Product
from products.forms.category import CategoryForm, CategorySearchForm


class CategoryListView(LoginRequiredMixin, FormMixin, ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    form_class = CategorySearchForm
    
    def get_form_kwargs(self):
        """Form için keyword argümanlarını alır."""
        kwargs = super().get_form_kwargs()
        # GET parametreleri varsa form'a aktar
        if self.request.method == 'GET':
            kwargs['data'] = self.request.GET.copy()
        return kwargs
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('parent').prefetch_related('products')
        
        # Form ile filtreleme
        form = self.get_form()
        if form.is_valid():
            queryset = form.filter_queryset(queryset)
        
        # Ürün sayılarını ekle
        queryset = queryset.annotate(
            product_count=Count('products'),
            active_product_count=Count('products', filter=Q(products__is_active=True))
        )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # İstatistikler
        categories = Category.objects.all()
        
        # Toplam kategori sayısı
        context['total_categories'] = categories.count()
        
        # Ana kategori sayısı
        context['root_category_count'] = categories.filter(parent__isnull=True).count()
        
        # Aktif/Pasif kategori sayıları
        context['active_category_count'] = categories.filter(is_active=True).count()
        context['inactive_category_count'] = categories.filter(is_active=False).count()
        
        # Aktif kategori yüzdesi
        if context['total_categories'] > 0:
            context['active_category_percentage'] = (context['active_category_count'] / context['total_categories']) * 100
        else:
            context['active_category_percentage'] = 0
        
        # Kategorili ürün sayısı ve yüzdesi
        total_products = Product.objects.count()
        products_with_category = Product.objects.filter(category__isnull=False).count()
        
        context['total_products'] = total_products
        context['products_with_category'] = products_with_category
        context['categorization_percentage'] = (products_with_category / total_products * 100) if total_products > 0 else 0
        
        # En büyük kategori
        largest_category = Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0).order_by('-product_count').first()
        
        if largest_category:
            context['largest_category'] = largest_category
            context['largest_category_percentage'] = (largest_category.product_count / total_products * 100) if total_products > 0 else 0
        
        # Son 30 günde eklenen kategoriler
        last_30_days = datetime.now() - timedelta(days=30)
        context['new_categories'] = categories.filter(created_at__gte=last_30_days).count()
        
        # Form context'e ekle
        context['form'] = self.get_form()
        
        # Sıralama URL'leri oluştur
        current_params = self.request.GET.copy()
        sort_urls = {}
        
        fields = ['name', 'product_count', 'created_at']
        for field in fields:
            params = current_params.copy()
            if current_params.get('sort_by') == field:
                params['sort_by'] = f'-{field}'
            else:
                params['sort_by'] = field
            sort_urls[field] = f"?{params.urlencode()}"
        
        context['sort_urls'] = sort_urls
        context['current_sort'] = current_params.get('sort_by', 'name')
        
        return context


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