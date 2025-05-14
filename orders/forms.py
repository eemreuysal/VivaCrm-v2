from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div
from django.utils import timezone

from customers.models import Customer, Address
from products.models import Product
from .models import Order, OrderItem, Payment, Shipment


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_number', 'customer', 'status', 'order_date', 'notes',
            'billing_address', 'shipping_address',
            'payment_method', 'payment_status', 'payment_notes',
            'shipping_cost', 'discount_amount',
            'owner'
        ]
        widgets = {
            'order_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'payment_notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'order-form'
        
        # Filter addresses by customer if order exists and has a customer
        if self.instance and self.instance.customer_id:
            self.fields['billing_address'].queryset = Address.objects.filter(customer=self.instance.customer)
            self.fields['shipping_address'].queryset = Address.objects.filter(customer=self.instance.customer)
        else:
            self.fields['billing_address'].queryset = Address.objects.none()
            self.fields['shipping_address'].queryset = Address.objects.none()
        
        # Create an auto-generated order number for new orders
        if not self.instance.pk and not self.instance.order_number:
            self.initial['order_number'] = f"ORD-{timezone.now().strftime('%Y%m%d')}-{Order.objects.count() + 1:04d}"
        
        self.helper.layout = Layout(
            Fieldset(
                _('Sipariş Bilgileri'),
                Row(
                    Column('order_number', css_class='form-group col-md-6 mb-0'),
                    Column('order_date', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('customer', css_class='form-group col-md-6 mb-0'),
                    Column('status', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('billing_address', css_class='form-group col-md-6 mb-0'),
                    Column('shipping_address', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'notes',
            ),
            Fieldset(
                _('Ödeme Bilgileri'),
                Row(
                    Column('payment_method', css_class='form-group col-md-6 mb-0'),
                    Column('payment_status', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'payment_notes',
            ),
            Fieldset(
                _('Fiyatlandırma'),
                Row(
                    Column('shipping_cost', css_class='form-group col-md-6 mb-0'),
                    Column('discount_amount', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _('Diğer Bilgiler'),
                'owner',
            ),
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'orders:order-list\' %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        billing_address = cleaned_data.get('billing_address')
        shipping_address = cleaned_data.get('shipping_address')
        
        # Validate that addresses belong to the selected customer
        if customer and billing_address and billing_address.customer != customer:
            self.add_error('billing_address', _('Fatura adresi seçilen müşteriye ait değil.'))
        
        if customer and shipping_address and shipping_address.customer != customer:
            self.add_error('shipping_address', _('Teslimat adresi seçilen müşteriye ait değil.'))
        
        return cleaned_data


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price', 'tax_rate', 'discount_amount', 'notes']
    
    def __init__(self, *args, **kwargs):
        order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'order-item-form'
        
        # Filter products to only include available ones
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        
        self.helper.layout = Layout(
            Row(
                Column('product', css_class='form-group col-md-6 mb-0'),
                Column('quantity', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('unit_price', css_class='form-group col-md-4 mb-0'),
                Column('tax_rate', css_class='form-group col-md-4 mb-0'),
                Column('discount_amount', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'notes',
            Div(
                Submit('submit', _('Ekle'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right mt-4'
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # If price is not specified, use product price
        if not instance.unit_price and instance.product:
            if instance.product.discount_price and instance.product.discount_price > 0:
                instance.unit_price = instance.product.discount_price
            else:
                instance.unit_price = instance.product.price
        
        # If tax rate is not specified, use product tax rate
        if not instance.tax_rate and instance.product:
            instance.tax_rate = instance.product.tax_rate
        
        if commit:
            instance.save()
        
        return instance


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount', 'payment_date', 'transaction_id', 'notes', 'is_successful']
        widgets = {
            'payment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'payment-form'
        
        # Set initial amount to remaining balance if order provided
        if order and not self.instance.pk:
            # Get total paid so far
            total_paid = sum(payment.amount for payment in order.payments.filter(is_successful=True))
            # Calculate remaining balance
            remaining = order.total_amount - total_paid
            if remaining > 0:
                self.initial['amount'] = remaining
            # Set initial payment method from order if available
            if order.payment_method:
                self.initial['payment_method'] = order.payment_method
        
        self.helper.layout = Layout(
            Row(
                Column('payment_method', css_class='form-group col-md-6 mb-0'),
                Column('amount', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('payment_date', css_class='form-group col-md-6 mb-0'),
                Column('transaction_id', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'notes',
            'is_successful',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right mt-4'
            )
        )


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['carrier', 'tracking_number', 'shipping_date', 'estimated_delivery', 'status', 'notes']
        widgets = {
            'shipping_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estimated_delivery': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'shipment-form'
        
        self.helper.layout = Layout(
            Row(
                Column('carrier', css_class='form-group col-md-6 mb-0'),
                Column('tracking_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('shipping_date', css_class='form-group col-md-6 mb-0'),
                Column('estimated_delivery', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'status',
            'notes',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>'),
                css_class='text-right mt-4'
            )
        )


class OrderSearchForm(forms.Form):
    query = forms.CharField(
        label=_('Ara'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Sipariş no, müşteri adı...')})
    )
    status = forms.ChoiceField(
        label=_('Durum'),
        required=False,
        choices=[('', _('Tümü'))] + list(Order.STATUS_CHOICES)
    )
    payment_status = forms.ChoiceField(
        label=_('Ödeme Durumu'),
        required=False,
        choices=[('', _('Tümü'))] + list(Order.PAYMENT_STATUS_CHOICES)
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'order-search-form'
        
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-4 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                Column('payment_status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('date_from', css_class='form-group col-md-4 mb-0'),
                Column('date_to', css_class='form-group col-md-4 mb-0'),
                Column(
                    HTML('<label class="form-control-label">&nbsp;</label><div><button type="submit" class="btn btn-primary btn-block">Ara</button></div>'),
                    css_class='form-group col-md-4 mb-0'
                ),
                css_class='form-row'
            ),
        )