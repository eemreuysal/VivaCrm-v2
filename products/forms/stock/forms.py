"""
Forms for stock management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML

from products.models import Product, StockMovement


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