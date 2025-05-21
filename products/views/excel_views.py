"""
Products modülü Excel view'ları.
Bu modül, Excel import/export işlemleri için view'ları içerir.
Facade pattern kullanılarak Excel işlemleri modülerleştirildi.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.views.generic import FormView, TemplateView, View
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q

from ..models import Product
from ..forms import ProductFilterForm, ExcelImportForm
from .excel_facade import ExcelImportFacade, ExcelExportFacade


class ProductExcelImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Ürün Excel import view'ı.
    Facade pattern kullanılarak Excel işlemleri modülerleştirildi.
    """
    template_name = 'products/excel_import.html'
    form_class = ExcelImportForm
    permission_required = 'products.add_product'
    
    def form_valid(self, form):
        """Excel dosyasını yükle ve import et"""
        # Excel import facade'ını kullan
        facade = ExcelImportFacade(self.request)
        return facade.handle_import_form(form)


class ProductExcelImportResultsView(LoginRequiredMixin, TemplateView):
    """
    Import sonuçlarını göster.
    Facade pattern kullanılarak Excel işlemleri modülerleştirildi.
    """
    template_name = 'products/excel_import_results.html'
    
    def get_context_data(self, **kwargs):
        """Import sonuçlarını context'e ekle"""
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get('session_id')
        
        # Excel import facade'ını kullan
        facade = ExcelImportFacade(self.request)
        results_data = facade.get_import_results(session_id)
        
        # Context'e ekle
        context.update(results_data)
        
        # Sonuçlar bulunamadı kontrol
        if not results_data.get('results') and not results_data.get('task'):
            context['error'] = 'Sonuçlar bulunamadı veya süresi doldu.'
        
        return context


class ProductExcelExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Ürünleri Excel'e export et.
    Facade pattern kullanılarak Excel işlemleri modülerleştirildi.
    """
    permission_required = 'products.view_product'
    
    def get(self, request, *args, **kwargs):
        """Export işlemi"""
        # Filtre parametrelerini al
        filter_form = ProductFilterForm(request.GET)
        queryset = self.get_filtered_queryset(filter_form)
        
        # Export tipini al
        export_type = request.GET.get('type', 'full')
        
        # Excel export facade'ını kullan
        facade = ExcelExportFacade(request)
        return facade.export_products(
            queryset, 
            export_type=export_type,
            use_chunks=queryset.count() > 5000
        )
    
    def get_filtered_queryset(self, filter_form):
        """Form'a göre queryset filtrele"""
        queryset = Product.objects.all()
        
        if filter_form.is_valid():
            # Kategori filtresi
            if filter_form.cleaned_data.get('category'):
                queryset = queryset.filter(
                    category=filter_form.cleaned_data['category']
                )
                
            # Durum filtresi
            if filter_form.cleaned_data.get('status'):
                queryset = queryset.filter(
                    status=filter_form.cleaned_data['status']
                )
                
            # Arama filtresi
            if filter_form.cleaned_data.get('search'):
                search_term = filter_form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(code__icontains=search_term) |
                    Q(sku__icontains=search_term)
                )
                
            # Fiyat aralığı
            if filter_form.cleaned_data.get('min_price'):
                queryset = queryset.filter(
                    price__gte=filter_form.cleaned_data['min_price']
                )
                
            if filter_form.cleaned_data.get('max_price'):
                queryset = queryset.filter(
                    price__lte=filter_form.cleaned_data['max_price']
                )
                
            # Stok filtresi
            if filter_form.cleaned_data.get('in_stock'):
                queryset = queryset.filter(current_stock__gt=0)
        
        return queryset


class ProductExcelTemplateView(LoginRequiredMixin, View):
    """
    Import için boş Excel template indir.
    Facade pattern kullanılarak Excel işlemleri modülerleştirildi.
    """
    
    def get(self, request, *args, **kwargs):
        """Template oluştur ve indir"""
        # Excel export facade'ını kullan
        facade = ExcelExportFacade(request)
        return facade.generate_template()


# Function-based views (geriye uyumluluk için)
@login_required
def product_excel_import_view(request):
    """Function-based import view"""
    view = ProductExcelImportView.as_view()
    return view(request)


@login_required
def product_excel_export_view(request):
    """Function-based export view"""
    view = ProductExcelExportView.as_view()
    return view(request)


@login_required
def product_excel_template_view(request):
    """Function-based template view"""
    view = ProductExcelTemplateView.as_view()
    return view(request)


@login_required
@require_POST
def validate_excel_file(request):
    """Excel dosyasını import öncesi doğrula (AJAX)"""
    if 'excel_file' not in request.FILES:
        return JsonResponse({'error': 'Dosya bulunamadı'}, status=400)
    
    excel_file = request.FILES['excel_file']
    
    # Excel import facade'ını kullan
    facade = ExcelImportFacade(request)
    validation_result = facade.validate_excel_file(excel_file)
    
    return JsonResponse(validation_result)


@login_required
def import_progress_api(request, session_id):
    """Import işlemi ilerleme durumu (AJAX)"""
    from django.core.cache import cache
    
    progress_data = cache.get(f'import_progress_{session_id}')
    
    # Asenkron task varsa durumunu kontrol et
    task_id = cache.get(f'import_task_{session_id}')
    if task_id:
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id)
        
        if task_result.ready() and task_result.successful():
            # Task tamamlandıysa sonuçları al
            progress_data = {
                'status': 'completed',
                'task_id': task_id,
                'result': task_result.result
            }
    
    if not progress_data:
        return JsonResponse({
            'status': 'not_found',
            'message': 'İlerleme bilgisi bulunamadı'
        }, status=404)
    
    return JsonResponse(progress_data)