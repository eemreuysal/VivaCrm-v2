"""
Forms for Excel import/export functionality.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, HTML


class ExcelImportForm(forms.Form):
    """
    Form for importing products from Excel file.
    """
    excel_file = forms.FileField(
        label=_('Excel Dosyası'),
        help_text=_('Excel dosyası seçin (.xlsx veya .xls formatında)'),
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'file-input file-input-bordered w-full'
        })
    )
    use_chunks = forms.BooleanField(
        label=_('Büyük Dosya Modu'),
        required=False,
        initial=True,
        help_text=_('Büyük dosyalar için bellek optimize modunu kullan')
    )
    skip_validation = forms.BooleanField(
        label=_('Validasyonu Atla'),
        required=False,
        initial=False,
        help_text=_('Doğrulama adımını atlayarak hızlı içe aktarma gerçekleştir')
    )
    async_import = forms.BooleanField(
        label=_('Arkaplanda Çalıştır'),
        required=False,
        initial=False,
        help_text=_('Uzun sürebilecek işlemleri arkaplanda çalıştır')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'excel-import-form'
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        
        self.helper.layout = Layout(
            'excel_file',
            'use_chunks',
            'skip_validation',
            'async_import',
            Div(
                Submit('submit', _('İçe Aktar'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'products:product-list\' %}" class="btn btn-secondary ml-2">İptal</a>'),
                css_class='text-right mt-4'
            )
        )
        
    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError(_('Yalnızca Excel dosyaları (.xlsx veya .xls) kabul edilir.'))
            
            # Check file size (max 25MB)
            if file.size > 25 * 1024 * 1024:
                raise forms.ValidationError(_('Dosya boyutu 25MB\'dan büyük olamaz.'))
                
        return file