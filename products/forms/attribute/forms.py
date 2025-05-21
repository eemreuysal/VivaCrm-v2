"""
Forms for product attribute management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML

from products.models import ProductAttribute, ProductAttributeValue


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
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        # Only show attributes that are not already assigned to this product
        if self.product:
            existing_attrs = self.product.attribute_values.values_list('attribute', flat=True)
            self.fields['attribute'].queryset = ProductAttribute.objects.exclude(id__in=existing_attrs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'product-attribute-value-form'
        
        self.helper.layout = Layout(
            'attribute',
            'value',
            Div(
                Submit('submit', _('Kaydet'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:product-detail\' slug=product.slug %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )