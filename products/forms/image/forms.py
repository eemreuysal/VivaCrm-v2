"""
Forms for product image management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML

from products.models import ProductImage


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'order']
        widgets = {
            'alt_text': forms.TextInput(attrs={'placeholder': _('Resim açıklaması (opsiyonel)')})
        }
        
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'product-image-form'
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        
        self.helper.layout = Layout(
            'image',
            'alt_text',
            Row(
                Column('is_primary', css_class='form-group col-md-6 mb-0'),
                Column('order', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', _('Yükle'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:product-detail\' slug=product.slug %}" class="btn btn-secondary">İptal</a>'),
                css_class='text-right mt-4'
            )
        )
        
    def clean(self):
        cleaned_data = super().clean()
        is_main = cleaned_data.get('is_main')
        
        # If marked as main, ensure no other main image exists
        if is_main and self.product:
            existing_main = self.product.images.filter(is_main=True)
            if self.instance.pk:
                existing_main = existing_main.exclude(pk=self.instance.pk)
            if existing_main.exists():
                # Instead of error, we'll update the other image
                existing_main.update(is_main=False)
        
        return cleaned_data