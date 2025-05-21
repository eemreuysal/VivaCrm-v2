# -*- coding: utf-8 -*-
from django.urls import path
from . import views_validation

app_name = 'core_validation'

urlpatterns = [
    # Main views
    path('', views_validation.validation_rules_list, name='validation_rules_list'),
    path('builder/', views_validation.validation_builder, name='validation_builder'),
    path('test/', views_validation.test_validation, name='test_validation'),
    path('demo/', views_validation.dynamic_form_demo, name='dynamic_form_demo'),
    path('logs/', views_validation.validation_logs, name='validation_logs'),
    
    # Rule management
    path('rules/create/', views_validation.create_validation_rule, name='create_validation_rule'),
    path('rules/<int:pk>/edit/', views_validation.edit_validation_rule, name='edit_validation_rule'),
    path('rules/<int:pk>/delete/', views_validation.delete_validation_rule, name='delete_validation_rule'),
    
    # Rule set management
    path('rule-sets/create/', views_validation.create_rule_set, name='create_rule_set'),
    path('rule-sets/<int:pk>/edit/', views_validation.edit_rule_set, name='edit_rule_set'),
    path('rule-sets/<int:pk>/delete/', views_validation.delete_rule_set, name='delete_rule_set'),
    
    # API endpoints
    path('api/rule-fields/', views_validation.get_rule_fields, name='get_rule_fields'),
]