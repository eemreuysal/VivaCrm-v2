# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.views.decorators.http import require_http_methods

from .models import ValidationRule, RuleSet, ValidationLog
from .forms_validation import (
    ValidationRuleForm, RuleSetForm, ValidationRuleFormSet,
    TestValidationForm, DynamicValidationForm
)
from .validation_rules import RuleRegistry, PresetRules
import json


@login_required
@permission_required('core.view_validationrule')
def validation_rules_list(request):
    """List all validation rules."""
    rules = ValidationRule.objects.all()
    rule_sets = RuleSet.objects.all()
    
    context = {
        'rules': rules,
        'rule_sets': rule_sets,
        'title': _('Doğrulama Kuralları')
    }
    return render(request, 'core/validation_rules.html', context)


@login_required
@permission_required('core.add_validationrule')
def create_validation_rule(request):
    """Create a new validation rule."""
    if request.method == 'POST':
        form = ValidationRuleForm(request.POST)
        if form.is_valid():
            rule_data = form.get_rule_data()
            rule = ValidationRule.objects.create(
                name=request.POST.get('rule_name', ''),
                rule_type=rule_data['type'],
                parameters={k: v for k, v in rule_data.items() if k not in ['type', 'message']},
                error_message=rule_data.get('message', '')
            )
            messages.success(request, _('Doğrulama kuralı başarıyla oluşturuldu.'))
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'rule_id': rule.id,
                    'rule_name': rule.name
                })
            
            return redirect('core:validation_rules_list')
    else:
        form = ValidationRuleForm()
    
    context = {
        'form': form,
        'title': _('Yeni Doğrulama Kuralı')
    }
    return render(request, 'core/validation_rule_form.html', context)


@login_required
@permission_required('core.change_validationrule')
def edit_validation_rule(request, pk):
    """Edit an existing validation rule."""
    rule = get_object_or_404(ValidationRule, pk=pk)
    
    if request.method == 'POST':
        form = ValidationRuleForm(request.POST)
        if form.is_valid():
            rule_data = form.get_rule_data()
            rule.rule_type = rule_data['type']
            rule.parameters = {k: v for k, v in rule_data.items() if k not in ['type', 'message']}
            rule.error_message = rule_data.get('message', '')
            rule.save()
            
            messages.success(request, _('Doğrulama kuralı başarıyla güncellendi.'))
            return redirect('core:validation_rules_list')
    else:
        # Pre-fill form with existing rule data
        initial_data = {
            'rule_type': rule.rule_type,
            'error_message': rule.error_message
        }
        initial_data.update(rule.parameters)
        form = ValidationRuleForm(initial=initial_data)
    
    context = {
        'form': form,
        'rule': rule,
        'title': _('Doğrulama Kuralını Düzenle')
    }
    return render(request, 'core/validation_rule_form.html', context)


@login_required
@permission_required('core.delete_validationrule')
@require_http_methods(["POST"])
def delete_validation_rule(request, pk):
    """Delete a validation rule."""
    rule = get_object_or_404(ValidationRule, pk=pk)
    rule.delete()
    messages.success(request, _('Doğrulama kuralı başarıyla silindi.'))
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('core:validation_rules_list')


@login_required
@permission_required('core.add_ruleset')
def create_rule_set(request):
    """Create a new rule set."""
    if request.method == 'POST':
        form = RuleSetForm(request.POST)
        formset = ValidationRuleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Create rule set
                rule_set = form.save(commit=False)
                rule_set.created_by = request.user
                rule_set.save()
                
                # Create rules and associate with rule set
                for rule_form in formset:
                    if rule_form.cleaned_data and not rule_form.cleaned_data.get('DELETE'):
                        rule_data = rule_form.get_rule_data()
                        rule = ValidationRule.objects.create(
                            name=f"{rule_set.name} - {rule_data['type']}",
                            rule_type=rule_data['type'],
                            parameters={k: v for k, v in rule_data.items() if k not in ['type', 'message']},
                            error_message=rule_data.get('message', '')
                        )
                        rule_set.rules.add(rule)
                
                messages.success(request, _('Kural seti başarıyla oluşturuldu.'))
                return redirect('core:validation_rules_list')
    else:
        form = RuleSetForm()
        formset = ValidationRuleFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': _('Yeni Kural Seti')
    }
    return render(request, 'core/rule_set_form.html', context)


@login_required
@permission_required('core.change_ruleset')
def edit_rule_set(request, pk):
    """Edit an existing rule set."""
    rule_set = get_object_or_404(RuleSet, pk=pk)
    
    if request.method == 'POST':
        form = RuleSetForm(request.POST, instance=rule_set)
        formset = ValidationRuleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Update rule set
                rule_set = form.save()
                
                # Clear existing rules
                rule_set.rules.clear()
                
                # Create new rules and associate with rule set
                for rule_form in formset:
                    if rule_form.cleaned_data and not rule_form.cleaned_data.get('DELETE'):
                        rule_data = rule_form.get_rule_data()
                        rule = ValidationRule.objects.create(
                            name=f"{rule_set.name} - {rule_data['type']}",
                            rule_type=rule_data['type'],
                            parameters={k: v for k, v in rule_data.items() if k not in ['type', 'message']},
                            error_message=rule_data.get('message', '')
                        )
                        rule_set.rules.add(rule)
                
                messages.success(request, _('Kural seti başarıyla güncellendi.'))
                return redirect('core:validation_rules_list')
    else:
        form = RuleSetForm(instance=rule_set)
        # Pre-fill formset with existing rules
        initial_data = []
        for rule in rule_set.rules.all():
            data = {
                'rule_type': rule.rule_type,
                'error_message': rule.error_message
            }
            data.update(rule.parameters)
            initial_data.append(data)
        
        formset = ValidationRuleFormSet(initial=initial_data)
    
    context = {
        'form': form,
        'formset': formset,
        'rule_set': rule_set,
        'title': _('Kural Setini Düzenle')
    }
    return render(request, 'core/rule_set_form.html', context)


@login_required
@permission_required('core.delete_ruleset')
@require_http_methods(["POST"])
def delete_rule_set(request, pk):
    """Delete a rule set."""
    rule_set = get_object_or_404(RuleSet, pk=pk)
    rule_set.delete()
    messages.success(request, _('Kural seti başarıyla silindi.'))
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('core:validation_rules_list')


@login_required
def validation_builder(request):
    """Interactive validation rule builder."""
    presets = {
        'turkish_phone': PresetRules.turkish_phone().build(),
        'email_address': PresetRules.email_address().build(),
        'turkish_id': PresetRules.turkish_id().build(),
        'price_field': PresetRules.price_field().build(),
        'percentage': PresetRules.percentage().build(),
        'stock_quantity': PresetRules.stock_quantity().build(),
        'website_url': PresetRules.website_url().build(),
        'company_name': PresetRules.company_name().build(),
        'tax_number': PresetRules.tax_number().build(),
    }
    
    # Convert presets to JSON-serializable format
    presets_json = {}
    for name, rules in presets.items():
        presets_json[name] = [rule.to_dict() for rule in rules]
    
    context = {
        'title': _('Doğrulama Kuralı Oluşturucu'),
        'presets': presets_json,
        'rule_types': ValidationRuleForm.RULE_TYPES
    }
    return render(request, 'core/validation_builder.html', context)


@login_required
def test_validation(request):
    """Test validation rules."""
    results = None
    
    if request.method == 'POST':
        form = TestValidationForm(request.POST)
        if form.is_valid():
            results = form.test_rules()
    else:
        form = TestValidationForm()
    
    context = {
        'form': form,
        'results': results,
        'title': _('Doğrulama Test Aracı')
    }
    return render(request, 'core/test_validation.html', context)


@login_required
def dynamic_form_demo(request):
    """Demo of dynamic form with validation rules."""
    # Get active rule sets
    rule_sets = RuleSet.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = DynamicValidationForm(rule_sets, request.POST)
        if form.is_valid():
            # Process form data
            messages.success(request, _('Form başarıyla doğrulandı!'))
            
            # Log validation
            for rule_set in rule_sets:
                field_name = f"{rule_set.model_name}_{rule_set.field_name}"
                value = form.cleaned_data.get(field_name)
                if value:
                    errors = rule_set.validate(value)
                    ValidationLog.objects.create(
                        rule_set=rule_set,
                        value=str(value),
                        is_valid=not bool(errors),
                        errors=errors
                    )
    else:
        form = DynamicValidationForm(rule_sets)
    
    context = {
        'form': form,
        'title': _('Dinamik Form Demo')
    }
    return render(request, 'core/dynamic_form.html', context)


@login_required
@require_http_methods(["GET"])
def get_rule_fields(request):
    """Get required fields for a specific rule type via AJAX."""
    rule_type = request.GET.get('rule_type')
    
    fields = {
        'regex': ['pattern'],
        'range': ['min_value', 'max_value'],
        'length': ['min_length', 'max_length'],
        'choices': ['choices'],
        'date': ['date_format'],
    }
    
    required_fields = fields.get(rule_type, [])
    
    return JsonResponse({
        'rule_type': rule_type,
        'required_fields': required_fields
    })


@login_required
def validation_logs(request):
    """View validation logs."""
    logs = ValidationLog.objects.select_related('rule_set').order_by('-created_at')[:100]
    
    context = {
        'logs': logs,
        'title': _('Doğrulama Logları')
    }
    return render(request, 'core/validation_logs.html', context)