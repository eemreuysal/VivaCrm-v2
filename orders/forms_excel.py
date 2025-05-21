"""
Excel import form for the Orders app.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div


class ExcelImportForm(forms.Form):
    """
    Form for importing orders from Excel files
    """
    excel_file = forms.FileField(
        label=_('Excel Dosyası'),
        required=True,
        help_text=_('Lütfen sipariş verilerini içeren bir Excel dosyası (.xlsx veya .xls) seçin.')
    )
    
    update_existing = forms.BooleanField(
        label=_('Mevcut siparişleri güncelle'),
        required=False,
        initial=False,
        help_text=_('İşaretlerseniz, mevcut siparişler güncellenir. İşaretlemezseniz, sadece yeni siparişler oluşturulur.')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'order-import-form'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                _('Sipariş Verileri İçe Aktar'),
                'excel_file',
                'update_existing',
                css_class='mb-3'
            ),
            Div(
                Submit('submit', _('İçe Aktar'), css_class='btn btn-primary'),
                HTML('<a href="{% url \'orders:generate-order-template\' %}" class="btn btn-secondary ml-2">Şablon İndir</a>'),
                css_class='text-right mt-3'
            )
        )