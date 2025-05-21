from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div
from .models import Customer, Address, Contact


class CustomerExcelImportForm(forms.Form):
    """
    Form for importing customers from Excel file.
    """
    excel_file = forms.FileField(
        label=_('Excel Dosyası'),
        help_text=_('Müşterileri içeren Excel dosyası (.xlsx)'),
        widget=forms.FileInput(attrs={'accept': '.xlsx', 'class': 'form-control'})
    )
    update_existing = forms.BooleanField(
        label=_('Mevcut müşterileri güncelle'),
        required=False,
        initial=True,
        help_text=_('E-posta adresi aynı olan müşterileri güncelle')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'customer-excel-import-form'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                _('Excel Import'),
                'excel_file',
                'update_existing',
            ),
            Div(
                Submit('submit', _('Yükle ve Import Et'), css_class='btn btn-primary'),
                HTML('<a href="{% url "customers:customer-list" %}" class="btn btn-secondary ml-2">İptal</a>'),
                HTML('<a href="{% url "customers:customer-excel-template" %}" class="btn btn-info ml-2">Boş Şablon İndir</a>'),
                css_class='text-right mt-3'
            )
        )
        
    def clean_excel_file(self):
        excel_file = self.cleaned_data.get('excel_file')
        if excel_file:
            if not excel_file.name.endswith('.xlsx'):
                raise forms.ValidationError(_('Lütfen geçerli bir Excel dosyası (.xlsx) yükleyin.'))
            if excel_file.size > 10 * 1024 * 1024:  # 10 MB
                raise forms.ValidationError(_('Dosya boyutu çok büyük. Maksimum 10 MB.'))
        return excel_file


class AddressExcelImportForm(forms.Form):
    """
    Form for importing addresses from Excel file.
    """
    excel_file = forms.FileField(
        label=_('Excel Dosyası'),
        help_text=_('Adresleri içeren Excel dosyası (.xlsx)'),
        widget=forms.FileInput(attrs={'accept': '.xlsx', 'class': 'form-control'})
    )
    update_existing = forms.BooleanField(
        label=_('Mevcut adresleri güncelle'),
        required=False,
        initial=True,
        help_text=_('Aynı başlığa sahip adresleri güncelle')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'address-excel-import-form'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                _('Adres Excel Import'),
                'excel_file',
                'update_existing',
            ),
            Div(
                Submit('submit', _('Yükle ve Import Et'), css_class='btn btn-primary'),
                HTML('<a href="{% url "customers:customer-list" %}" class="btn btn-secondary ml-2">İptal</a>'),
                HTML('<a href="{% url "customers:address-excel-template" %}" class="btn btn-info ml-2">Boş Şablon İndir</a>'),
                css_class='text-right mt-3'
            )
        )
        
    def clean_excel_file(self):
        excel_file = self.cleaned_data.get('excel_file')
        if excel_file:
            if not excel_file.name.endswith('.xlsx'):
                raise forms.ValidationError(_('Lütfen geçerli bir Excel dosyası (.xlsx) yükleyin.'))
            if excel_file.size > 10 * 1024 * 1024:  # 10 MB
                raise forms.ValidationError(_('Dosya boyutu çok büyük. Maksimum 10 MB.'))
        return excel_file


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'type', 'company_name', 'tax_office', 'tax_number', 
                 'email', 'phone', 'website', 'notes', 'owner', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'customer-form'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-10'
        
        self.helper.layout = Layout(
            Fieldset(
                _('Temel Bilgiler'),
                Row(
                    Column('name', css_class='form-group col-md-6 mb-0'),
                    Column('type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('email', css_class='form-group col-md-6 mb-0'),
                    Column('phone', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'website',
            ),
            Fieldset(
                _('Şirket Bilgileri'),
                Div(
                    'company_name',
                    Row(
                        Column('tax_office', css_class='form-group col-md-6 mb-0'),
                        Column('tax_number', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='company-fields',
                    data_display_condition="type === 'corporate'"
                )
            ),
            Fieldset(
                _('Ek Bilgiler'),
                'notes',
                Row(
                    Column('owner', css_class='form-group col-md-6 mb-0'),
                    Column('is_active', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'customers:customer-list\' %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right'
            )
        )


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['title', 'type', 'address_line1', 'address_line2', 'city', 
                 'state', 'postal_code', 'country', 'is_default']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'address-form'
        
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-6 mb-0'),
                Column('type', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'address_line1',
            'address_line2',
            Row(
                Column('city', css_class='form-group col-md-4 mb-0'),
                Column('state', css_class='form-group col-md-4 mb-0'),
                Column('postal_code', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'country',
            'is_default',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right'
            )
        )


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'title', 'department', 'email', 'phone', 'is_primary', 'notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'contact-form'
        
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('title', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-0'),
                Column('phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'department',
            'notes',
            'is_primary',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right'
            )
        )
        

class CustomerSearchForm(forms.Form):
    query = forms.CharField(
        label=_('Ara'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Müşteri adı, e-posta veya telefon')})
    )
    customer_type = forms.ChoiceField(
        label=_('Müşteri Tipi'),
        required=False,
        choices=[('', _('Hepsi'))] + list(Customer.CUSTOMER_TYPE_CHOICES)
    )
    is_active = forms.BooleanField(
        label=_('Sadece Aktif Müşteriler'),
        required=False,
        initial=True
    )
    sort_by = forms.ChoiceField(
        label=_('Sıralama'),
        required=False,
        choices=[
            ('name', _('İsim')),
            ('created_at', _('Kayıt Tarihi')),
            ('total_orders', _('Sipariş Sayısı')),
            ('total_revenue', _('Toplam Ciro')),
        ],
        initial='name'
    )
    sort_dir = forms.ChoiceField(
        label=_('Sıralama Yönü'),
        required=False,
        choices=[
            ('asc', _('Artan')),
            ('desc', _('Azalan')),
        ],
        initial='asc'
    )
    created_from = forms.DateField(
        label=_('Oluşturulma Başlangıç'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    created_to = forms.DateField(
        label=_('Oluşturulma Bitiş'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    min_orders = forms.IntegerField(
        label=_('Min Sipariş'),
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': _('Min sipariş sayısı')})
    )
    min_revenue = forms.DecimalField(
        label=_('Min Ciro'),
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': _('Min ciro')})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'customer-search-form'
        self.helper.form_class = 'form-inline'
        
        self.helper.layout = Layout(
            'query',
            'customer_type',
            'is_active',
            Submit('search', _('Ara'), css_class='btn btn-primary ml-2')
        )
        
class CustomerFilterForm(forms.Form):
    """
    Form for filtering customers for export functionality.
    """
    query = forms.CharField(
        label=_('Arama Terimi'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Müşteri adı, e-posta veya telefon')})
    )
    customer_type = forms.ChoiceField(
        label=_('Müşteri Tipi'),
        required=False,
        choices=[('', _('Hepsi'))] + list(Customer.CUSTOMER_TYPE_CHOICES)
    )
    is_active = forms.ChoiceField(
        label=_('Durum'),
        required=False,
        choices=[
            ('', _('Hepsi')),
            ('true', _('Aktif')),
            ('false', _('Pasif')),
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
        self.helper.form_id = 'customer-filter-form'
        
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-6 mb-0'),
                Column('customer_type', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_active', css_class='form-group col-md-4 mb-0'),
                Column('created_from', css_class='form-group col-md-4 mb-0'),
                Column('created_to', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Div(
                Submit('filter', _('Filtrele'), css_class='btn btn-primary'),
                HTML('<a href="{% url "customers:export_customers" %}" class="btn btn-secondary ml-2">Sıfırla</a>'),
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
                models.Q(email__icontains=query) |
                models.Q(phone__icontains=query) |
                models.Q(company_name__icontains=query)
            )
            
        if self.cleaned_data.get('customer_type'):
            queryset = queryset.filter(type=self.cleaned_data['customer_type'])
            
        if self.cleaned_data.get('is_active') == 'true':
            queryset = queryset.filter(is_active=True)
        elif self.cleaned_data.get('is_active') == 'false':
            queryset = queryset.filter(is_active=False)
            
        if self.cleaned_data.get('created_from'):
            queryset = queryset.filter(created_at__gte=self.cleaned_data['created_from'])
            
        if self.cleaned_data.get('created_to'):
            queryset = queryset.filter(created_at__lte=self.cleaned_data['created_to'])
            
        return queryset