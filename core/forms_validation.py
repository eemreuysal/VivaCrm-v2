# -*- coding: utf-8 -*-
from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _
from .validation_rules import RuleRegistry, RuleBuilder
import json


class ValidationRuleForm(forms.Form):
    """Form for creating validation rules."""
    
    RULE_TYPES = [
        ('required', _('Zorunlu Alan')),
        ('regex', _('Regex (Düzenli İfade)')),
        ('range', _('Sayı Aralığı')),
        ('length', _('Metin Uzunluğu')),
        ('choices', _('Seçenekler')),
        ('email', _('E-posta')),
        ('phone', _('Telefon')),
        ('url', _('URL')),
        ('tckn', _('TC Kimlik No')),
        ('date', _('Tarih')),
    ]
    
    rule_type = forms.ChoiceField(
        choices=RULE_TYPES,
        label=_('Kural Tipi'),
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'})
    )
    
    # Regex parameters
    pattern = forms.CharField(
        label=_('Regex Deseni'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': r'^\d{10}$'
        })
    )
    
    # Range parameters
    min_value = forms.DecimalField(
        label=_('Minimum Değer'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'step': '0.01'
        })
    )
    
    max_value = forms.DecimalField(
        label=_('Maksimum Değer'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'step': '0.01'
        })
    )
    
    # Length parameters
    min_length = forms.IntegerField(
        label=_('Minimum Uzunluk'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'min': '0'
        })
    )
    
    max_length = forms.IntegerField(
        label=_('Maksimum Uzunluk'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'min': '0'
        })
    )
    
    # Choices parameter
    choices = forms.CharField(
        label=_('Seçenekler (virgülle ayırarak)'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'seçenek1, seçenek2, seçenek3'
        })
    )
    
    # Date format
    date_format = forms.CharField(
        label=_('Tarih Formatı'),
        required=False,
        initial='%Y-%m-%d',
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '%Y-%m-%d'
        })
    )
    
    # Error message
    error_message = forms.CharField(
        label=_('Hata Mesajı'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Özel hata mesajı (opsiyonel)')
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        rule_type = cleaned_data.get('rule_type')
        
        # Validate required fields based on rule type
        if rule_type == 'regex' and not cleaned_data.get('pattern'):
            raise forms.ValidationError(_('Regex kuralı için desen zorunludur'))
        
        if rule_type == 'range':
            if not cleaned_data.get('min_value') and not cleaned_data.get('max_value'):
                raise forms.ValidationError(_('Aralık kuralı için en az bir sınır belirtilmelidir'))
        
        if rule_type == 'length':
            if not cleaned_data.get('min_length') and not cleaned_data.get('max_length'):
                raise forms.ValidationError(_('Uzunluk kuralı için en az bir sınır belirtilmelidir'))
        
        if rule_type == 'choices' and not cleaned_data.get('choices'):
            raise forms.ValidationError(_('Seçenek kuralı için seçenekler belirtilmelidir'))
        
        if rule_type == 'date' and not cleaned_data.get('date_format'):
            raise forms.ValidationError(_('Tarih kuralı için format belirtilmelidir'))
        
        return cleaned_data
    
    def get_rule_data(self):
        """Convert form data to rule dictionary."""
        data = self.cleaned_data
        rule_type = data['rule_type']
        
        rule_data = {
            'type': rule_type,
            'message': data.get('error_message', '')
        }
        
        if rule_type == 'regex':
            rule_data['pattern'] = data['pattern']
        elif rule_type == 'range':
            if data.get('min_value') is not None:
                rule_data['min_value'] = str(data['min_value'])
            if data.get('max_value') is not None:
                rule_data['max_value'] = str(data['max_value'])
        elif rule_type == 'length':
            if data.get('min_length') is not None:
                rule_data['min_length'] = data['min_length']
            if data.get('max_length') is not None:
                rule_data['max_length'] = data['max_length']
        elif rule_type == 'choices':
            choices = [c.strip() for c in data['choices'].split(',') if c.strip()]
            rule_data['choices'] = choices
        elif rule_type == 'date':
            rule_data['format'] = data['date_format']
        
        return rule_data


class RuleSetForm(forms.Form):
    """Form for creating rule sets."""
    
    name = forms.CharField(
        label=_('Kural Seti Adı'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Örn: Müşteri Doğrulama Kuralları')
        })
    )
    
    description = forms.CharField(
        label=_('Açıklama'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': _('Bu kural setinin açıklaması')
        })
    )
    
    model_name = forms.CharField(
        label=_('Model Adı'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Örn: Customer')
        })
    )
    
    field_name = forms.CharField(
        label=_('Alan Adı'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Örn: phone_number')
        })
    )
    
    is_active = forms.BooleanField(
        label=_('Aktif'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'})
    )


ValidationRuleFormSet = formset_factory(
    ValidationRuleForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class DynamicValidationForm(forms.Form):
    """Dynamically generated form with validation rules."""
    
    def __init__(self, rule_sets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for rule_set in rule_sets:
            field_name = f"{rule_set.model_name}_{rule_set.field_name}"
            field_label = rule_set.field_name.replace('_', ' ').title()
            
            # Create field based on validation rules
            field = self._create_field(rule_set)
            self.fields[field_name] = field
    
    def _create_field(self, rule_set):
        """Create form field based on rule set."""
        # Analyze rules to determine field type
        rules = rule_set.get_rules()
        
        # Default to CharField
        field_class = forms.CharField
        widget_class = forms.TextInput
        widget_attrs = {'class': 'input input-bordered w-full'}
        
        # Check for specific rule types
        for rule in rules:
            rule_type = rule.get('type')
            
            if rule_type == 'email':
                field_class = forms.EmailField
                widget_class = forms.EmailInput
            elif rule_type == 'url':
                field_class = forms.URLField
                widget_class = forms.URLInput
            elif rule_type == 'choices':
                field_class = forms.ChoiceField
                widget_class = forms.Select
                # Set choices from rule
                choices = [(c, c) for c in rule.get('choices', [])]
                field_kwargs = {'choices': choices}
            elif rule_type == 'range':
                # If numeric range, use number field
                field_class = forms.DecimalField
                widget_class = forms.NumberInput
                widget_attrs['step'] = '0.01'
                
                # Set min/max from rule
                field_kwargs = {}
                if 'min_value' in rule:
                    field_kwargs['min_value'] = rule['min_value']
                if 'max_value' in rule:
                    field_kwargs['max_value'] = rule['max_value']
            elif rule_type == 'date':
                field_class = forms.DateField
                widget_class = forms.DateInput
                widget_attrs['type'] = 'date'
        
        # Create widget
        widget = widget_class(attrs=widget_attrs)
        
        # Create field
        field_kwargs = field_kwargs if 'field_kwargs' in locals() else {}
        field_kwargs.update({
            'label': rule_set.field_name.replace('_', ' ').title(),
            'required': any(r['type'] == 'required' for r in rules),
            'widget': widget,
            'help_text': rule_set.description
        })
        
        field = field_class(**field_kwargs)
        
        # Add custom validators
        field.validators.extend(self._create_validators(rules))
        
        return field
    
    def _create_validators(self, rules):
        """Create Django validators from rule set."""
        validators = []
        
        for rule_data in rules:
            rule = RuleRegistry.create_from_dict(rule_data)
            if rule:
                validators.append(rule)
        
        return validators


class TestValidationForm(forms.Form):
    """Form for testing validation rules."""
    
    test_value = forms.CharField(
        label=_('Test Değeri'),
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Test edilecek değeri girin')
        })
    )
    
    rules_json = forms.CharField(
        label=_('Kurallar (JSON)'),
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full font-mono',
            'rows': 10,
            'placeholder': json.dumps([
                {
                    "type": "required",
                    "message": "Bu alan zorunludur"
                },
                {
                    "type": "email",
                    "message": "Geçerli bir e-posta adresi girin"
                }
            ], indent=2, ensure_ascii=False)
        })
    )
    
    def clean_rules_json(self):
        """Parse and validate JSON rules."""
        rules_json = self.cleaned_data['rules_json']
        try:
            rules = json.loads(rules_json)
            if not isinstance(rules, list):
                raise forms.ValidationError(_('Kurallar bir liste olmalıdır'))
            return rules
        except json.JSONDecodeError as e:
            raise forms.ValidationError(_('Geçersiz JSON formatı: {}').format(str(e)))
    
    def test_rules(self):
        """Test the value against the rules."""
        if not self.is_valid():
            return None
        
        test_value = self.cleaned_data['test_value']
        rules_data = self.cleaned_data['rules_json']
        
        results = []
        for rule_data in rules_data:
            rule = RuleRegistry.create_from_dict(rule_data)
            if rule:
                try:
                    rule(test_value)
                    results.append({
                        'rule': rule_data,
                        'status': 'success',
                        'message': _('Doğrulama başarılı')
                    })
                except forms.ValidationError as e:
                    results.append({
                        'rule': rule_data,
                        'status': 'error',
                        'message': str(e.message)
                    })
            else:
                results.append({
                    'rule': rule_data,
                    'status': 'error',
                    'message': _('Kural oluşturulamadı')
                })
        
        return results