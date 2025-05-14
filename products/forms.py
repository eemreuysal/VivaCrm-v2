from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import models 
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div
from .models import (
    Category, Product, ProductImage, ProductAttribute, 
    ProductAttributeValue, StockMovement
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent', 'description', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # To avoid recursive categories
        if self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(pk=self.instance.pk)
            
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'category-form'
        
        self.helper.layout = Layout(
            'name',
            'parent',
            'description',
            'is_active',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:category-list\' %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'code', 'name', 'category', 'description', 
            'price', 'cost', 'tax_rate', 'discount_price',
            'stock', 'is_physical', 'weight', 'dimensions', 'sku', 'barcode',
            'status', 'is_featured', 'is_active'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'product-form'
        
        self.helper.layout = Layout(
            Fieldset(
                _('Temel Bilgiler'),
                Row(
                    Column('code', css_class='form-group col-md-4 mb-0'),
                    Column('name', css_class='form-group col-md-8 mb-0'),
                    css_class='form-row'
                ),
                'category',
                'description',
            ),
            Fieldset(
                _('Fiyat ve Vergi'),
                Row(
                    Column('price', css_class='form-group col-md-3 mb-0'),
                    Column('cost', css_class='form-group col-md-3 mb-0'),
                    Column('tax_rate', css_class='form-group col-md-3 mb-0'),
                    Column('discount_price', css_class='form-group col-md-3 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _('Stok ve Fiziksel Özellikler'),
                Row(
                    Column('stock', css_class='form-group col-md-3 mb-0'),
                    Column('is_physical', css_class='form-group col-md-3 mb-0'),
                    css_class='form-row'
                ),
                Div(
                    Row(
                        Column('weight', css_class='form-group col-md-3 mb-0'),
                        Column('dimensions', css_class='form-group col-md-3 mb-0'),
                        Column('sku', css_class='form-group col-md-3 mb-0'),
                        Column('barcode', css_class='form-group col-md-3 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='physical-fields',
                    data_display_condition="is_physical"
                ),
            ),
            Fieldset(
                _('Durum'),
                Row(
                    Column('status', css_class='form-group col-md-4 mb-0'),
                    Column('is_featured', css_class='form-group col-md-4 mb-0'),
                    Column('is_active', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            ),
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:product-list\' %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'order']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'product-image-form'
        
        self.helper.layout = Layout(
            'image',
            'alt_text',
            Row(
                Column('is_primary', css_class='form-group col-md-6 mb-0'),
                Column('order', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right mt-4'
            )
        )


class ProductAttributeForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        fields = ['name', 'description', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'product-attribute-form'
        
        self.helper.layout = Layout(
            'name',
            'description',
            'is_active',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:attribute-list\' %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )


class ProductAttributeValueForm(forms.ModelForm):
    class Meta:
        model = ProductAttributeValue
        fields = ['attribute', 'value']
        
    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if product:
            # Filter attributes that haven't been used for this product yet
            used_attrs = ProductAttributeValue.objects.filter(product=product).values_list('attribute', flat=True)
            self.fields['attribute'].queryset = ProductAttribute.objects.filter(is_active=True).exclude(id__in=used_attrs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'product-attribute-value-form'
        
        self.helper.layout = Layout(
            'attribute',
            'value',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right mt-4'
            )
        )


class ProductSearchForm(forms.Form):
    query = forms.CharField(
        label=_('Ara'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Ürün adı, kodu veya barkod')})
    )
    category = forms.ModelChoiceField(
        label=_('Kategori'),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label=_('Tüm Kategoriler')
    )
    status = forms.ChoiceField(
        label=_('Durum'),
        required=False,
        choices=[('', _('Tümü'))] + list(Product.STATUS_CHOICES)
    )
    in_stock = forms.BooleanField(
        label=_('Sadece Stokta Olanlar'),
        required=False,
        initial=False
    )
    low_stock = forms.BooleanField(
        label=_('Düşük Stok Uyarısı Olanlar'),
        required=False,
        initial=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'product-search-form'
        self.helper.form_class = 'form-inline'
        
        self.helper.layout = Layout(
            'query',
            'category',
            'status',
            'in_stock',
            'low_stock',
            Submit('search', _('Ara'), css_class='btn btn-primary ml-2')
        )


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'movement_type', 'quantity', 'unit_cost', 'reference', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only active products for selection
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        
        # Make fields required based on movement type
        self.fields['movement_type'].widget.attrs.update({
            'hx-get': '/products/movement-fields/',
            'hx-target': '#dynamic-fields',
            'hx-trigger': 'change',
            'hx-swap': 'innerHTML'
        })
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'stock-movement-form'
        
        self.helper.layout = Layout(
            Row(
                Column('product', css_class='form-group col-md-6 mb-0'),
                Column('movement_type', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Div(
                id='dynamic-fields',
                css_class='form-row'
            ),
            Row(
                Column('quantity', css_class='form-group col-md-6 mb-0'),
                Column('unit_cost', css_class='form-group col-md-6 mb-0', 
                       data_display_condition="movement_type == 'purchase'"),
                css_class='form-row'
            ),
            Row(
                Column('reference', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'notes',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:movement-list\' %}" class="btn btn-secondary ml-2">İptal</a>'),
                css_class='mt-4'
            )
        )
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class BulkStockAdjustmentForm(forms.Form):
    ADJUSTMENT_TYPE_CHOICES = (
        ('absolute', _('Kesin Değer')),
        ('increase', _('Arttır')),
        ('decrease', _('Azalt')),
    )
    
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True, is_physical=True),
        label=_('Ürünler'),
        widget=forms.SelectMultiple(attrs={'size': 10, 'class': 'select2'})
    )
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPE_CHOICES,
        label=_('Ayarlama Tipi'),
        initial='increase'
    )
    quantity = forms.IntegerField(
        label=_('Miktar'),
        min_value=0
    )
    notes = forms.CharField(
        label=_('Notlar'),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'bulk-stock-adjustment-form'
        
        self.helper.layout = Layout(
            'products',
            Row(
                Column('adjustment_type', css_class='form-group col-md-6 mb-0'),
                Column('quantity', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'notes',
            Div(
                Submit('submit', _('Stok Ayarla'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:product-list\' %}" class="btn btn-secondary ml-2">İptal</a>'),
                css_class='mt-4'
            )
        )
        
class ProductFilterForm(forms.Form):
    """
    Form for filtering products for export functionality.
    """
    query = forms.CharField(
        label=_('Arama Terimi'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Ürün adı, kodu veya barkod')})
    )
    category = forms.ModelChoiceField(
        label=_('Kategori'),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label=_('Tüm Kategoriler')
    )
    status = forms.ChoiceField(
        label=_('Durum'),
        required=False,
        choices=[('', _('Tümü'))] + list(Product.STATUS_CHOICES)
    )
    is_active = forms.ChoiceField(
        label=_('Aktiflik'),
        required=False,
        choices=[
            ('', _('Hepsi')),
            ('true', _('Aktif')),
            ('false', _('Pasif')),
        ]
    )
    stock_status = forms.ChoiceField(
        label=_('Stok Durumu'),
        required=False,
        choices=[
            ('', _('Hepsi')),
            ('in_stock', _('Stokta')),
            ('out_of_stock', _('Stokta Yok')),
            ('low_stock', _('Düşük Stok')),
        ]
    )
    created_from = forms.DateField(
        label=_('Oluşturulma Tarihi (Başlangıç)'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    created_to = forms.DateField(
        label=_('Oluşturulma Tarihi (Bitiş)'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'product-filter-form'
        
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-6 mb-0'),
                Column('category', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('status', css_class='form-group col-md-4 mb-0'),
                Column('is_active', css_class='form-group col-md-4 mb-0'),
                Column('stock_status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('created_from', css_class='form-group col-md-6 mb-0'),
                Column('created_to', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Div(
                Submit('filter', _('Filtrele'), css_class='btn btn-primary'),
                HTML('<a href="{% url "products:export_products" %}" class="btn btn-secondary ml-2">Sıfırla</a>'),
                css_class='text-right mt-3'
            )
        )
        
    def filter_queryset(self, queryset):
        """
        Apply the filters to a queryset based on form data.
        """
        if self.cleaned_data.get('query'):
            query = self.cleaned_data['query']
            queryset = queryset.filter(
                models.Q(name__icontains=query) |
                models.Q(code__icontains=query) |
                models.Q(barcode__icontains=query) |
                models.Q(sku__icontains=query)
            )
            
        if self.cleaned_data.get('category'):
            queryset = queryset.filter(category=self.cleaned_data['category'])
            
        if self.cleaned_data.get('status'):
            queryset = queryset.filter(status=self.cleaned_data['status'])
            
        if self.cleaned_data.get('is_active') == 'true':
            queryset = queryset.filter(is_active=True)
        elif self.cleaned_data.get('is_active') == 'false':
            queryset = queryset.filter(is_active=False)
            
        if self.cleaned_data.get('stock_status') == 'in_stock':
            queryset = queryset.filter(stock__gt=0)
        elif self.cleaned_data.get('stock_status') == 'out_of_stock':
            queryset = queryset.filter(stock=0)
        elif self.cleaned_data.get('stock_status') == 'low_stock':
            # Assuming there's a low_stock_threshold defined somewhere
            queryset = queryset.filter(stock__gt=0, stock__lte=models.F('low_stock_threshold'))
            
        if self.cleaned_data.get('created_from'):
            queryset = queryset.filter(created_at__gte=self.cleaned_data['created_from'])
            
        if self.cleaned_data.get('created_to'):
            queryset = queryset.filter(created_at__lte=self.cleaned_data['created_to'])
            
        return queryset