from django.views.generic import TemplateView, ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import redirect
import json
from datetime import datetime, timedelta

from .models import SavedReport
from .forms import SalesReportForm, ProductReportForm, CustomerReportForm, SaveReportForm
from .services import ReportService


class ReportDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view for reports.
    """
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get some basic stats for the dashboard
        # Sales summary for the current month
        today = timezone.now().date()
        first_day = today.replace(day=1)
        context['sales_summary'] = ReportService.get_sales_summary(start_date=first_day)
        
        # Top 5 products this month
        context['top_products'] = ReportService.get_top_products(limit=5, start_date=first_day)
        
        # Top 5 customers this month
        context['top_customers'] = ReportService.get_top_customers(limit=5, start_date=first_day)
        
        # Inventory status summary
        inventory_status = ReportService.get_inventory_status()
        context['inventory_summary'] = inventory_status['summary']
        
        # Payment method distribution this month
        context['payment_stats'] = ReportService.get_payment_statistics(start_date=first_day)
        
        # User's saved reports
        context['saved_reports'] = SavedReport.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')[:5]
        
        return context


class SalesReportView(LoginRequiredMixin, TemplateView):
    """
    Sales report view.
    """
    template_name = 'reports/sales_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SalesReportForm(self.request.GET or None)
        
        if context['form'].is_valid():
            # Get parameters from form
            cleaned_data = context['form'].cleaned_data
            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')
            grouping = cleaned_data.get('grouping') or 'month'
            status = cleaned_data.get('status')
            
            # Generate report data
            context['sales_summary'] = ReportService.get_sales_summary(
                start_date=start_date, 
                end_date=end_date,
                status=status
            )
            
            context['sales_by_period'] = ReportService.get_sales_by_period(
                period=grouping,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
            
            # Add top products and payment stats
            context['top_products'] = ReportService.get_top_products(
                limit=5,
                start_date=start_date,
                end_date=end_date
            )
            
            context['payment_stats'] = ReportService.get_payment_statistics(
                start_date=start_date,
                end_date=end_date
            )
            
            # Data for saving the report
            context['save_form'] = SaveReportForm(initial={
                'name': f"Satış Raporu ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})",
                'type': 'sales',
                'description': f"Satış raporu: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}, Gruplama: {grouping}"
            })
            
            # Store parameters for saving
            context['report_parameters'] = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'grouping': grouping,
                'status': status
            }
        
        return context


class ProductReportView(LoginRequiredMixin, TemplateView):
    """
    Product report view.
    """
    template_name = 'reports/product_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProductReportForm(self.request.GET or None)
        
        if context['form'].is_valid():
            # Get parameters from form
            cleaned_data = context['form'].cleaned_data
            report_type = cleaned_data.get('report_type')
            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')
            limit = cleaned_data.get('limit') or 10
            category = cleaned_data.get('category')
            low_stock_threshold = cleaned_data.get('low_stock_threshold') or 10
            
            # Generate report data based on type
            if report_type == 'top_products':
                context['top_products'] = ReportService.get_top_products(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('En Çok Satan Ürünler')
                
            elif report_type == 'top_categories':
                context['top_categories'] = ReportService.get_top_categories(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('En Çok Satan Kategoriler')
                
            elif report_type == 'inventory':
                inventory_status = ReportService.get_inventory_status(
                    category=category,
                    low_stock_threshold=low_stock_threshold
                )
                context['inventory_summary'] = inventory_status['summary']
                context['inventory_products'] = inventory_status['products']
                context['report_title'] = _('Stok Durumu')
            
            # Data for saving the report
            context['save_form'] = SaveReportForm(initial={
                'name': f"{context.get('report_title')} ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})",
                'type': 'product',
                'description': f"Ürün raporu: {context.get('report_title')}, {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
            })
            
            # Store parameters for saving
            context['report_parameters'] = {
                'report_type': report_type,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'limit': limit,
                'category_id': category.id if category else None,
                'low_stock_threshold': low_stock_threshold
            }
        
        return context


class CustomerReportView(LoginRequiredMixin, TemplateView):
    """
    Customer report view.
    """
    template_name = 'reports/customer_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CustomerReportForm(self.request.GET or None)
        
        if context['form'].is_valid():
            # Get parameters from form
            cleaned_data = context['form'].cleaned_data
            report_type = cleaned_data.get('report_type')
            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')
            limit = cleaned_data.get('limit') or 10
            grouping = cleaned_data.get('grouping') or 'month'
            
            # Generate report data based on type
            if report_type == 'top_customers':
                context['top_customers'] = ReportService.get_top_customers(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('En İyi Müşteriler')
                
            elif report_type == 'acquisition':
                context['customer_acquisition'] = ReportService.get_customer_acquisition(
                    period=grouping,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('Müşteri Kazanımı')
            
            # Data for saving the report
            context['save_form'] = SaveReportForm(initial={
                'name': f"{context.get('report_title')} ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})",
                'type': 'customer',
                'description': f"Müşteri raporu: {context.get('report_title')}, {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
            })
            
            # Store parameters for saving
            context['report_parameters'] = {
                'report_type': report_type,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'limit': limit,
                'grouping': grouping
            }
        
        return context


class SavedReportListView(LoginRequiredMixin, ListView):
    """
    View for listing saved reports.
    """
    model = SavedReport
    template_name = 'reports/saved_report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        # Get user's reports and shared reports
        return SavedReport.objects.filter(
            owner=self.request.user
        ) | SavedReport.objects.filter(
            is_shared=True
        ).exclude(
            owner=self.request.user
        )


class SavedReportDetailView(LoginRequiredMixin, DetailView):
    """
    View for viewing a saved report.
    """
    model = SavedReport
    template_name = 'reports/saved_report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        
        # Generate report data based on saved parameters
        parameters = report.parameters
        
        if report.type == 'sales':
            # Convert ISO format strings to datetime objects
            start_date = datetime.fromisoformat(parameters.get('start_date')).date()
            end_date = datetime.fromisoformat(parameters.get('end_date')).date()
            grouping = parameters.get('grouping', 'month')
            status = parameters.get('status')
            
            context['sales_summary'] = ReportService.get_sales_summary(
                start_date=start_date, 
                end_date=end_date,
                status=status
            )
            
            context['sales_by_period'] = ReportService.get_sales_by_period(
                period=grouping,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
            
            context['top_products'] = ReportService.get_top_products(
                limit=5,
                start_date=start_date,
                end_date=end_date
            )
            
            context['payment_stats'] = ReportService.get_payment_statistics(
                start_date=start_date,
                end_date=end_date
            )
            
        elif report.type == 'product':
            report_type = parameters.get('report_type')
            start_date = datetime.fromisoformat(parameters.get('start_date')).date() if parameters.get('start_date') else None
            end_date = datetime.fromisoformat(parameters.get('end_date')).date() if parameters.get('end_date') else None
            limit = parameters.get('limit', 10)
            
            if report_type == 'top_products':
                context['top_products'] = ReportService.get_top_products(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('En Çok Satan Ürünler')
                
            elif report_type == 'top_categories':
                context['top_categories'] = ReportService.get_top_categories(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('En Çok Satan Kategoriler')
                
            elif report_type == 'inventory':
                from products.models import Category
                category_id = parameters.get('category_id')
                category = Category.objects.get(id=category_id) if category_id else None
                low_stock_threshold = parameters.get('low_stock_threshold', 10)
                
                inventory_status = ReportService.get_inventory_status(
                    category=category,
                    low_stock_threshold=low_stock_threshold
                )
                context['inventory_summary'] = inventory_status['summary']
                context['inventory_products'] = inventory_status['products']
                context['report_title'] = _('Stok Durumu')
                
        elif report.type == 'customer':
            report_type = parameters.get('report_type')
            start_date = datetime.fromisoformat(parameters.get('start_date')).date() if parameters.get('start_date') else None
            end_date = datetime.fromisoformat(parameters.get('end_date')).date() if parameters.get('end_date') else None
            limit = parameters.get('limit', 10)
            grouping = parameters.get('grouping', 'month')
            
            if report_type == 'top_customers':
                context['top_customers'] = ReportService.get_top_customers(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('En İyi Müşteriler')
                
            elif report_type == 'acquisition':
                context['customer_acquisition'] = ReportService.get_customer_acquisition(
                    period=grouping,
                    start_date=start_date,
                    end_date=end_date
                )
                context['report_title'] = _('Müşteri Kazanımı')
        
        return context


class SaveReportView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    View for saving a report.
    """
    model = SavedReport
    form_class = SaveReportForm
    template_name = 'reports/save_report.html'
    success_message = _("Rapor başarıyla kaydedildi.")
    success_url = reverse_lazy('reports:saved-report-list')
    
    def form_valid(self, form):
        # Set owner to current user
        form.instance.owner = self.request.user
        
        # Set parameters from POST data
        parameters_json = self.request.POST.get('parameters')
        if parameters_json:
            form.instance.parameters = json.loads(parameters_json)
        
        return super().form_valid(form)


class SavedReportDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    View for deleting a saved report.
    """
    model = SavedReport
    template_name = 'reports/saved_report_confirm_delete.html'
    success_url = reverse_lazy('reports:saved-report-list')
    success_message = _("Rapor başarıyla silindi.")
    
    def get_queryset(self):
        # Only allow deleting user's own reports
        return SavedReport.objects.filter(owner=self.request.user)