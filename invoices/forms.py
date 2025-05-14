from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div

from .models import Invoice, InvoiceItem


class InvoiceForm(forms.ModelForm):
    """
    Form for creating and updating invoices.
    """
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'invoice_type', 'status', 
            'issue_date', 'due_date', 'notes'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'invoice-form'
        
        # Auto-generate invoice number if not provided (for new invoices)
        if not self.instance.pk and not self.initial.get('invoice_number'):
            year = timezone.now().year
            month = timezone.now().month
            # Get count of invoices for this month
            count = Invoice.objects.filter(
                issue_date__year=year, 
                issue_date__month=month
            ).count() + 1
            
            self.initial['invoice_number'] = f"INV-{year}{month:02d}-{count:04d}"
        
        # If editing existing invoice, disable order field
        if self.instance.pk:
            self.fields['invoice_number'].disabled = True
        
        # Layout for the form
        self.helper.layout = Layout(
            Fieldset(
                _('Fatura Bilgileri'),
                Row(
                    Column('invoice_number', css_class='form-group col-md-4 mb-0'),
                    Column('invoice_type', css_class='form-group col-md-4 mb-0'),
                    Column('status', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('issue_date', css_class='form-group col-md-6 mb-0'),
                    Column('due_date', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _('Ek Bilgiler'),
                'notes',
            ),
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% if invoice.pk %}{% url "invoices:invoice-detail" pk=invoice.pk %}{% else %}{% url "invoices:invoice-list" %}{% endif %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # If this is a new invoice and order is provided
        if not instance.pk and self.order:
            instance.order = self.order
            
            # Copy amounts from order
            instance.subtotal = self.order.subtotal
            instance.tax_amount = self.order.tax_amount
            instance.shipping_cost = self.order.shipping_cost
            instance.discount_amount = self.order.discount_amount
            instance.total_amount = self.order.total_amount
            
        if commit:
            instance.save()
            
            # If this is a new invoice and order is provided, create invoice items
            if not self.instance.pk and self.order:
                for order_item in self.order.items.all():
                    InvoiceItem.objects.create(
                        invoice=instance,
                        description=f"{order_item.product.name} (x{order_item.quantity})",
                        quantity=order_item.quantity,
                        unit_price=order_item.unit_price,
                        tax_rate=order_item.tax_rate,
                        discount_amount=order_item.discount_amount
                    )
                
        return instance


class InvoiceItemForm(forms.ModelForm):
    """
    Form for creating and updating invoice items.
    """
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'tax_rate', 'discount_amount']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'invoice-item-form'
        
        # Layout for the form
        self.helper.layout = Layout(
            Row(
                Column('description', css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('quantity', css_class='form-group col-md-3 mb-0'),
                Column('unit_price', css_class='form-group col-md-3 mb-0'),
                Column('tax_rate', css_class='form-group col-md-3 mb-0'),
                Column('discount_amount', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right mt-4'
            )
        )


class InvoiceSearchForm(forms.Form):
    """
    Form for searching invoices.
    """
    query = forms.CharField(
        label=_('Arama'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Fatura numarası, sipariş numarası...')})
    )
    
    status = forms.ChoiceField(
        label=_('Durum'),
        choices=[('', _('Tümü'))] + list(Invoice.STATUS_CHOICES),
        required=False
    )
    
    start_date = forms.DateField(
        label=_('Başlangıç Tarihi'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    end_date = forms.DateField(
        label=_('Bitiş Tarihi'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    show_paid = forms.BooleanField(
        label=_('Ödenenler'),
        required=False,
        initial=True
    )
    
    show_unpaid = forms.BooleanField(
        label=_('Ödenmeyenler'),
        required=False,
        initial=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'invoice-search-form'
        
        # Layout for the form
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-6 mb-0'),
                Column('status', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('end_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(
                    Div(
                        Div('show_paid', css_class='form-check form-check-inline'),
                        Div('show_unpaid', css_class='form-check form-check-inline'),
                    ),
                    css_class='form-group col-md-6 mb-0'
                ),
                Column(
                    Submit('search', _('Ara'), css_class='btn btn-primary'),
                    HTML('<a href="{% url "invoices:invoice-list" %}" class="btn btn-secondary ml-2">Temizle</a>'),
                    css_class='form-group col-md-6 mb-0 text-right'
                ),
                css_class='form-row align-items-end'
            ),
        )