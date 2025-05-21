"""
Forms for category management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, HTML

from products.models import Category


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


class CategorySearchForm(forms.Form):
    query = forms.CharField(
        label=_('Arama'), 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Kategori adı veya açıklama...')})
    )
    parent = forms.ModelChoiceField(
        label=_('Üst Kategori'),
        queryset=Category.objects.filter(parent__isnull=True, is_active=True),
        required=False,
        empty_label=_('Tüm Kategoriler')
    )
    is_active = forms.ChoiceField(
        label=_('Durum'),
        required=False,
        choices=[
            ('', _('Tümü')),
            ('true', _('Aktif')),
            ('false', _('Pasif')),
        ]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_id = 'category-search-form'
        self.helper.form_class = 'form-inline'
        
        self.helper.layout = Layout(
            'query',
            'parent',
            'is_active',
            Submit('search', _('Ara'), css_class='btn btn-primary ml-2')
        )
    
    def filter_queryset(self, queryset):
        """Filter the category queryset based on form data."""
        if not self.is_valid():
            return queryset
            
        query = self.cleaned_data.get('query')
        parent = self.cleaned_data.get('parent')
        is_active = self.cleaned_data.get('is_active')
        
        if query:
            queryset = queryset.filter(
                models.Q(name__icontains=query) |
                models.Q(description__icontains=query)
            )
        
        if parent:
            queryset = queryset.filter(parent=parent)
        
        if is_active:
            if is_active == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'false':
                queryset = queryset.filter(is_active=False)
        
        return queryset