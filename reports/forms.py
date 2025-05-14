from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div
from datetime import datetime, timedelta
from django.utils import timezone

from products.models import Category
from .models import SavedReport


class DateRangeForm(forms.Form):
    """
    Form for selecting a date range.
    """
    PERIOD_CHOICES = (
        ('today', _('Bugün')),
        ('yesterday', _('Dün')),
        ('this_week', _('Bu Hafta')),
        ('last_week', _('Geçen Hafta')),
        ('this_month', _('Bu Ay')),
        ('last_month', _('Geçen Ay')),
        ('this_year', _('Bu Yıl')),
        ('last_year', _('Geçen Yıl')),
        ('custom', _('Özel Aralık')),
    )
    
    period = forms.ChoiceField(
        label=_('Zaman Aralığı'),
        choices=PERIOD_CHOICES,
        required=False,
        initial='this_month'
    )
    
    start_date = forms.DateField(
        label=_('Başlangıç Tarihi'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'custom-date-input'})
    )
    
    end_date = forms.DateField(
        label=_('Bitiş Tarihi'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'custom-date-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'date-range-form'
        
        self.helper.layout = Layout(
            Row(
                Column('period', css_class='form-group col-md-4 mb-0'),
                Column('start_date', css_class='form-group col-md-4 mb-0 date-field'),
                Column('end_date', css_class='form-group col-md-4 mb-0 date-field'),
                css_class='form-row'
            ),
            Submit('submit', _('Uygula'), css_class='btn btn-primary mt-2')
        )
        
        # Set default dates
        if not self.is_bound:
            # Default to this month
            today = timezone.now().date()
            first_day = today.replace(day=1)
            self.initial['start_date'] = first_day
            self.initial['end_date'] = today
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # If a predefined period is selected, calculate the date range
        if period and period != 'custom':
            today = timezone.now().date()
            
            if period == 'today':
                start_date = today
                end_date = today
            elif period == 'yesterday':
                yesterday = today - timedelta(days=1)
                start_date = yesterday
                end_date = yesterday
            elif period == 'this_week':
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif period == 'last_week':
                start_date = today - timedelta(days=today.weekday() + 7)
                end_date = today - timedelta(days=today.weekday() + 1)
            elif period == 'this_month':
                start_date = today.replace(day=1)
                end_date = today
            elif period == 'last_month':
                if today.month == 1:
                    start_date = today.replace(year=today.year-1, month=12, day=1)
                    end_date = today.replace(year=today.year-1, month=12, day=31)
                else:
                    start_date = today.replace(month=today.month-1, day=1)
                    # Calculate last day of previous month
                    if today.month == 3:  # March
                        last_day = 28
                        if today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0):
                            last_day = 29
                    elif today.month in [5, 7, 10, 12]:  # May, July, October, December
                        last_day = 30
                    else:
                        last_day = 31
                    end_date = today.replace(month=today.month-1, day=last_day)
            elif period == 'this_year':
                start_date = today.replace(month=1, day=1)
                end_date = today
            elif period == 'last_year':
                start_date = today.replace(year=today.year-1, month=1, day=1)
                end_date = today.replace(year=today.year-1, month=12, day=31)
                
            cleaned_data['start_date'] = start_date
            cleaned_data['end_date'] = end_date
        
        # Validate that start_date <= end_date
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("Başlangıç tarihi bitiş tarihinden sonra olamaz."))
            
        return cleaned_data


class SalesReportForm(DateRangeForm):
    """
    Form for generating sales reports.
    """
    GROUPING_CHOICES = (
        ('day', _('Günlük')),
        ('week', _('Haftalık')),
        ('month', _('Aylık')),
    )
    
    STATUS_CHOICES = (
        ('', _('Tüm Siparişler')),
        ('completed', _('Tamamlanan')),
        ('cancelled', _('İptal Edilen')),
        ('processing', _('İşlemde')),
    )
    
    grouping = forms.ChoiceField(
        label=_('Gruplama'),
        choices=GROUPING_CHOICES,
        required=False,
        initial='month'
    )
    
    status = forms.ChoiceField(
        label=_('Sipariş Durumu'),
        choices=STATUS_CHOICES,
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'sales-report-form'
        
        self.helper.layout = Layout(
            Row(
                Column('period', css_class='form-group col-md-3 mb-0'),
                Column('start_date', css_class='form-group col-md-3 mb-0 date-field'),
                Column('end_date', css_class='form-group col-md-3 mb-0 date-field'),
                Column(
                    HTML('<label class="form-control-label mt-4 pt-1">&nbsp;</label><div><button type="submit" name="action" value="generate" class="btn btn-primary">Rapor Oluştur</button></div>'),
                    css_class='form-group col-md-3 mb-0'
                ),
                css_class='form-row'
            ),
            Row(
                Column('grouping', css_class='form-group col-md-6 mb-0'),
                Column('status', css_class='form-group col-md-6 mb-0'),
                css_class='form-row mt-2'
            ),
        )


class ProductReportForm(DateRangeForm):
    """
    Form for generating product reports.
    """
    REPORT_TYPE_CHOICES = (
        ('top_products', _('En Çok Satan Ürünler')),
        ('top_categories', _('En Çok Satan Kategoriler')),
        ('inventory', _('Stok Durumu')),
    )
    
    report_type = forms.ChoiceField(
        label=_('Rapor Tipi'),
        choices=REPORT_TYPE_CHOICES,
        required=True,
        initial='top_products'
    )
    
    limit = forms.IntegerField(
        label=_('Satır Sayısı'),
        required=False,
        initial=10,
        min_value=1,
        max_value=100
    )
    
    category = forms.ModelChoiceField(
        label=_('Kategori'),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label=_('Tüm Kategoriler')
    )
    
    low_stock_threshold = forms.IntegerField(
        label=_('Düşük Stok Eşiği'),
        required=False,
        initial=10,
        min_value=1
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'product-report-form'
        
        self.helper.layout = Layout(
            Row(
                Column('report_type', css_class='form-group col-md-6 mb-0'),
                Column('limit', css_class='form-group col-md-6 mb-0 limit-field'),
                css_class='form-row'
            ),
            Div(
                Row(
                    Column('period', css_class='form-group col-md-4 mb-0'),
                    Column('start_date', css_class='form-group col-md-4 mb-0 date-field'),
                    Column('end_date', css_class='form-group col-md-4 mb-0 date-field'),
                    css_class='form-row'
                ),
                css_class='sales-fields'
            ),
            Div(
                Row(
                    Column('category', css_class='form-group col-md-6 mb-0'),
                    Column('low_stock_threshold', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                css_class='inventory-fields'
            ),
            Submit('submit', _('Rapor Oluştur'), css_class='btn btn-primary mt-2')
        )


class CustomerReportForm(DateRangeForm):
    """
    Form for generating customer reports.
    """
    REPORT_TYPE_CHOICES = (
        ('top_customers', _('En İyi Müşteriler')),
        ('acquisition', _('Müşteri Kazanımı')),
    )
    
    GROUPING_CHOICES = (
        ('day', _('Günlük')),
        ('week', _('Haftalık')),
        ('month', _('Aylık')),
    )
    
    report_type = forms.ChoiceField(
        label=_('Rapor Tipi'),
        choices=REPORT_TYPE_CHOICES,
        required=True,
        initial='top_customers'
    )
    
    limit = forms.IntegerField(
        label=_('Satır Sayısı'),
        required=False,
        initial=10,
        min_value=1,
        max_value=100
    )
    
    grouping = forms.ChoiceField(
        label=_('Gruplama'),
        choices=GROUPING_CHOICES,
        required=False,
        initial='month'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'customer-report-form'
        
        self.helper.layout = Layout(
            Row(
                Column('report_type', css_class='form-group col-md-6 mb-0'),
                Div(
                    Column('limit', css_class='form-group col-md-6 mb-0'),
                    css_class='top-customers-fields'
                ),
                Div(
                    Column('grouping', css_class='form-group col-md-6 mb-0'),
                    css_class='acquisition-fields'
                ),
                css_class='form-row'
            ),
            Row(
                Column('period', css_class='form-group col-md-4 mb-0'),
                Column('start_date', css_class='form-group col-md-4 mb-0 date-field'),
                Column('end_date', css_class='form-group col-md-4 mb-0 date-field'),
                css_class='form-row'
            ),
            Submit('submit', _('Rapor Oluştur'), css_class='btn btn-primary mt-2')
        )


class SaveReportForm(forms.ModelForm):
    """
    Form for saving a report.
    """
    class Meta:
        model = SavedReport
        fields = ['name', 'type', 'description', 'is_shared']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'save-report-form'
        
        self.helper.layout = Layout(
            'name',
            'type',
            'description',
            'is_shared',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right mt-4'
            )
        )