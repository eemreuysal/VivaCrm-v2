"""
Forms for product management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import models 
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div

from products.models import Category, ProductFamily, Product, ProductAttribute, ProductAttributeValue


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'code', 'category', 'family', 'description',
            'price', 'cost', 'tax_rate', 'discount_price',
            'stock', 'threshold_stock', 'is_physical', 'weight', 'dimensions',
            'sku', 'barcode', 'status', 'is_featured', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'dimensions': forms.TextInput(attrs={'placeholder': _('Uzunluk x Genişlik x Yükseklik')}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Category choices with indentation
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['family'].queryset = ProductFamily.objects.filter(is_active=True)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'product-form'
        
        self.helper.layout = Layout(
            Fieldset(
                _('Temel Bilgiler'),
                Row(
                    Column('name', css_class='form-group col-md-8 mb-0'),
                    Column('code', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('category', css_class='form-group col-md-6 mb-0'),
                    Column('family', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
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
                _('Envanter'),
                Row(
                    Column('stock', css_class='form-group col-md-6 mb-0'),
                    Column('threshold_stock', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('is_physical', css_class='form-group col-md-4 mb-0'),
                    Column('weight', css_class='form-group col-md-4 mb-0'),
                    Column('dimensions', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _('Tanımlayıcılar'),
                Row(
                    Column('sku', css_class='form-group col-md-6 mb-0'),
                    Column('barcode', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
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
                Submit('submit_and_continue', _('Kaydet ve Devam Et'), css_class='btn btn-success'),
                HTML('<a href="{% url \'products:product-list\' %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )
        
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            # Check if code is unique (excluding current instance if editing)
            qs = Product.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_('Bu ürün kodu zaten kullanılıyor.'))
        return code
    
    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            # Check if barcode is unique (excluding current instance if editing)
            qs = Product.objects.filter(barcode=barcode)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_('Bu barkod zaten kullanılıyor.'))
        return barcode
        
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            # Check if SKU is unique (excluding current instance if editing)
            qs = Product.objects.filter(sku=sku)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_('Bu SKU zaten kullanılıyor.'))
        return sku
        
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        
        if price and discount_price:
            if discount_price >= price:
                self.add_error('discount_price', _('İndirimli fiyat, normal fiyattan düşük olmalıdır.'))
        
        return cleaned_data


class ProductSearchForm(forms.Form):
    query = forms.CharField(
        label=_('Arama'), 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Ürün adı, kodu veya barkod...')})
    )
    category = forms.ModelChoiceField(
        label=_('Kategori'),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label=_('Tüm Kategoriler')
    )
    family = forms.ModelChoiceField(
        label=_('Ürün Ailesi'),
        queryset=ProductFamily.objects.filter(is_active=True),
        required=False,
        empty_label=_('Tüm Aileler')
    )
    price_min = forms.DecimalField(
        label=_('Min Fiyat'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
    price_max = forms.DecimalField(
        label=_('Max Fiyat'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
    stock_status = forms.ChoiceField(
        label=_('Stok Durumu'),
        required=False,
        choices=[
            ('', _('Tümü')),
            ('in_stock', _('Stokta')),
            ('low_stock', _('Düşük Stok')),
            ('out_of_stock', _('Stokta Yok')),
        ]
    )
    status = forms.ChoiceField(
        label=_('Durum'),
        required=False,
        choices=[('', _('Tümü'))] + list(Product.STATUS_CHOICES)
    )
    ordering = forms.ChoiceField(
        label=_('Sıralama'),
        required=False,
        choices=[
            ('-created_at', _('En Yeni')),
            ('created_at', _('En Eski')),
            ('name', _('İsim (A-Z)')),
            ('-name', _('İsim (Z-A)')),
            ('price', _('Fiyat (Düşük > Yüksek)')),
            ('-price', _('Fiyat (Yüksek > Düşük)')),
            ('-stock', _('Stok (Yüksek > Düşük)')),
            ('stock', _('Stok (Düşük > Yüksek)')),
        ]
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
            'family',
            'price_min',
            'price_max',
            'stock_status',
            'status',
            'ordering',
            Submit('search', _('Ara'), css_class='btn btn-primary ml-2')
        )


class ProductAdvancedSearchForm(forms.Form):
    """
    Advanced search form for products with multiple criteria.
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
    family = forms.ModelChoiceField(
        label=_('Ürün Ailesi'),
        queryset=ProductFamily.objects.filter(is_active=True),
        required=False,
        empty_label=_('Tüm Aileler')
    )
    color = forms.ChoiceField(
        label=_('Renk'),
        required=False,
        choices=[]
    )
    size = forms.ChoiceField(
        label=_('Beden'),
        required=False,
        choices=[]
    )
    price_min = forms.DecimalField(
        label=_('Min Fiyat'),
        required=False,
        min_value=0,
        decimal_places=2
    )
    price_max = forms.DecimalField(
        label=_('Max Fiyat'),
        required=False,
        min_value=0,
        decimal_places=2
    )
    sales_count = forms.IntegerField(
        label=_('Min Satış Adeti'),
        required=False,
        min_value=0
    )
    date_from = forms.DateField(
        label=_('Başlangıç Tarihi'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        label=_('Bitiş Tarihi'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    status = forms.ChoiceField(
        label=_('Durum'),
        required=False,
        choices=[('', _('Tümü'))] + list(Product.STATUS_CHOICES)
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
            'family',
            'color',
            'size',
            'price_min',
            'price_max',
            'sales_count',
            Row(
                Column('date_from', css_class='form-group col-md-6 mb-0'),
                Column('date_to', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'status',
            Submit('search', _('Ara'), css_class='btn btn-primary ml-2')
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
        """Filter the product queryset based on form data."""
        if not self.is_valid():
            return queryset
            
        query = self.cleaned_data.get('query')
        category = self.cleaned_data.get('category')
        status = self.cleaned_data.get('status')
        is_active = self.cleaned_data.get('is_active')
        stock_status = self.cleaned_data.get('stock_status')
        created_from = self.cleaned_data.get('created_from')
        created_to = self.cleaned_data.get('created_to')
        
        if query:
            queryset = queryset.filter(
                models.Q(name__icontains=query) |
                models.Q(code__icontains=query) |
                models.Q(barcode__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(category=category)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if is_active:
            if is_active == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'false':
                queryset = queryset.filter(is_active=False)
        
        if stock_status:
            if stock_status == 'in_stock':
                queryset = queryset.filter(stock__gt=0)
            elif stock_status == 'out_of_stock':
                queryset = queryset.filter(stock=0)
            elif stock_status == 'low_stock':
                # Threshold'un altındaki ürünler
                queryset = queryset.exclude(stock=0).filter(
                    stock__lte=models.F('threshold_stock')
                )
        
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)
        
        return queryset