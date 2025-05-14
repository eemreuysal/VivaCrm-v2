"""
Views for Excel import/export functionality in the Customers app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from django.utils.decorators import method_decorator
import logging

from .models import Customer, Address
from .forms import CustomerFilterForm
from .excel import (export_customers_excel, export_customers_csv, 
                   generate_customer_import_template, import_customers_excel,
                   export_addresses_excel, generate_address_import_template,
                   import_addresses_excel)

logger = logging.getLogger(__name__)


@login_required
def export_customers(request, format='excel'):
    """
    Export customers to Excel or CSV format.
    """
    # Get filtered queryset
    filter_form = CustomerFilterForm(request.GET)
    queryset = Customer.objects.all()
    
    if filter_form.is_valid():
        queryset = filter_form.filter_queryset(queryset)
    
    # Export based on format
    if format == 'csv':
        return export_customers_csv(queryset)
    else:
        return export_customers_excel(queryset)


@login_required
def export_addresses(request, format='excel'):
    """
    Export customer addresses to Excel.
    """
    # Get filtered queryset of customers first
    filter_form = CustomerFilterForm(request.GET)
    customer_queryset = Customer.objects.all()
    
    if filter_form.is_valid():
        customer_queryset = filter_form.filter_queryset(customer_queryset)
    
    # Then get addresses for those customers
    address_queryset = Address.objects.filter(customer__in=customer_queryset)
    
    return export_addresses_excel(address_queryset)


@login_required
def generate_customer_template(request):
    """
    Generate and download a customer import template.
    """
    return generate_customer_import_template()


@login_required
def generate_address_template(request):
    """
    Generate and download an address import template.
    """
    return generate_address_import_template()


@method_decorator(login_required, name='dispatch')
class CustomerImportView(FormView):
    """
    View for importing customers from Excel.
    """
    template_name = 'customers/customer_import.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        # Check if file was provided
        if 'excel_file' not in request.FILES:
            messages.error(request, "No file was uploaded.")
            return render(request, self.template_name)
        
        file_obj = request.FILES['excel_file']
        update_existing = request.POST.get('update_existing', 'off') == 'on'
        
        # Validate file type
        if not file_obj.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Invalid file format. Please upload an Excel file (.xlsx or .xls).")
            return render(request, self.template_name)
        
        try:
            # Perform the import
            result = import_customers_excel(file_obj, update_existing)
            
            # Report results
            messages.success(
                request, 
                f"Import completed: {result['created']} customers created, "
                f"{result['updated']} customers updated, "
                f"{result['error_count']} errors."
            )
            
            # Handle errors
            if result['error_count'] > 0:
                error_details = []
                for error in result['error_rows']:
                    error_details.append(f"Row {error['row']}: {error['error']}")
                
                context = {
                    'success_count': result['created'] + result['updated'],
                    'error_count': result['error_count'],
                    'error_details': error_details,
                    'total': result['total']
                }
                return render(request, 'customers/import_results.html', context)
            
            # Redirect to customer list on success
            return redirect('customers:customer_list')
            
        except Exception as e:
            logger.error(f"Error importing customers: {str(e)}")
            messages.error(request, f"Error importing customers: {str(e)}")
            return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
class AddressImportView(FormView):
    """
    View for importing customer addresses from Excel.
    """
    template_name = 'customers/address_import.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        # Check if file was provided
        if 'excel_file' not in request.FILES:
            messages.error(request, "No file was uploaded.")
            return render(request, self.template_name)
        
        file_obj = request.FILES['excel_file']
        update_existing = request.POST.get('update_existing', 'off') == 'on'
        
        # Validate file type
        if not file_obj.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Invalid file format. Please upload an Excel file (.xlsx or .xls).")
            return render(request, self.template_name)
        
        try:
            # Perform the import
            result = import_addresses_excel(file_obj, update_existing)
            
            # Report results
            messages.success(
                request, 
                f"Import completed: {result['created']} addresses created, "
                f"{result['updated']} addresses updated, "
                f"{result['error_count']} errors."
            )
            
            # Handle errors
            if result['error_count'] > 0:
                error_details = []
                for error in result['error_rows']:
                    error_details.append(f"Row {error['row']}: {error['error']}")
                
                context = {
                    'success_count': result['created'] + result['updated'],
                    'error_count': result['error_count'],
                    'error_details': error_details,
                    'total': result['total'],
                    'import_type': 'address'
                }
                return render(request, 'customers/import_results.html', context)
            
            # Redirect to customer list on success
            return redirect('customers:customer_list')
            
        except Exception as e:
            logger.error(f"Error importing addresses: {str(e)}")
            messages.error(request, f"Error importing addresses: {str(e)}")
            return render(request, self.template_name)