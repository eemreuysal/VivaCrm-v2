"""
Views for Excel import/export functionality in the Products app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic import FormView, TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
import logging

from .models import Product, StockMovement
from .forms import ProductFilterForm
from .excel import (export_products_excel, export_products_csv, 
                   generate_product_import_template, import_products_excel,
                   export_stock_excel, generate_stock_adjustment_template,
                   import_stock_adjustments)

logger = logging.getLogger(__name__)


@login_required
def export_products(request, format='excel'):
    """
    Export products to Excel or CSV format.
    """
    # Get filtered queryset
    filter_form = ProductFilterForm(request.GET)
    queryset = Product.objects.all()
    
    if filter_form.is_valid():
        queryset = filter_form.filter_queryset(queryset)
    
    # Export based on format
    if format == 'csv':
        return export_products_csv(queryset)
    else:
        return export_products_excel(queryset)


@login_required
def export_stock(request, format='excel'):
    """
    Export stock information to Excel.
    """
    # Get filtered queryset
    filter_form = ProductFilterForm(request.GET)
    queryset = Product.objects.all()
    
    if filter_form.is_valid():
        queryset = filter_form.filter_queryset(queryset)
    
    return export_stock_excel(queryset)


@login_required
def generate_product_template(request):
    """
    Generate and download a product import template.
    """
    return generate_product_import_template()


@login_required
def generate_stock_template(request):
    """
    Generate and download a stock adjustment template.
    """
    return generate_stock_adjustment_template()


@method_decorator(login_required, name='dispatch')
class ProductImportView(FormView):
    """
    View for importing products from Excel.
    """
    template_name = 'products/product_import.html'
    
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
            result = import_products_excel(file_obj, update_existing)
            
            # Report results
            messages.success(
                request, 
                f"Import completed: {result['created']} products created, "
                f"{result['updated']} products updated, "
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
                return render(request, 'products/product_import_results.html', context)
            
            # Redirect to product list on success
            return redirect('products:product_list')
            
        except Exception as e:
            logger.error(f"Error importing products: {str(e)}")
            messages.error(request, f"Error importing products: {str(e)}")
            return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
class StockAdjustmentImportView(FormView):
    """
    View for importing stock adjustments from Excel.
    """
    template_name = 'products/stock_adjustment_import.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        # Check if file was provided
        if 'excel_file' not in request.FILES:
            messages.error(request, "No file was uploaded.")
            return render(request, self.template_name)
        
        file_obj = request.FILES['excel_file']
        
        # Validate file type
        if not file_obj.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Invalid file format. Please upload an Excel file (.xlsx or .xls).")
            return render(request, self.template_name)
        
        try:
            # Perform the import
            result = import_stock_adjustments(file_obj)
            
            # Report results
            messages.success(
                request, 
                f"Import completed: {result['success_count']} stock adjustments processed, "
                f"{result['error_count']} errors."
            )
            
            # Handle errors
            if result['error_count'] > 0:
                error_details = []
                for error in result['error_rows']:
                    error_details.append(f"Row {error['row']}: {error['error']}")
                
                context = {
                    'success_count': result['success_count'],
                    'error_count': result['error_count'],
                    'error_details': error_details,
                    'total': result['total']
                }
                return render(request, 'products/stock_adjustment_results.html', context)
            
            # Redirect to stock movement list on success
            return redirect('products:stock_movement_list')
            
        except Exception as e:
            logger.error(f"Error importing stock adjustments: {str(e)}")
            messages.error(request, f"Error importing stock adjustments: {str(e)}")
            return render(request, self.template_name)