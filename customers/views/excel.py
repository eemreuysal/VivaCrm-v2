"""
Customers modülü Excel view'ları.
Tüm Excel import/export işlemleri için tek giriş noktası.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.generic import FormView, TemplateView, View
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.http import require_POST
import logging
import uuid
import os
import tempfile

from ..models import Customer, Address
from ..forms import CustomerFilterForm, CustomerExcelImportForm, AddressExcelImportForm
from ..excel import CustomerExcelManager
from core.excel.exceptions import ExcelError

logger = logging.getLogger(__name__)


class CustomerExcelView:
    """
    Excel işlemleri için base view class.
    Diğer Excel view'ları bu sınıfı extend eder.
    """
    model = Customer
    permission_required = None  # Alt sınıflar belirler
    
    def __init__(self):
        self.excel_manager = CustomerExcelManager()


class CustomerExcelImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView, CustomerExcelView):
    """Müşteri Excel import view'ı"""
    template_name = 'customers/excel_import.html'
    form_class = CustomerExcelImportForm
    permission_required = 'customers.add_customer'
    success_url = None
    
    def get_success_url(self):
        """Import sonuçları sayfasına yönlendir"""
        return reverse('customers:excel-import-results', 
                      kwargs={'session_id': self.session_id})
    
    def form_valid(self, form):
        """Excel dosyasını yükle ve import et"""
        excel_file = form.cleaned_data['excel_file']
        update_existing = form.cleaned_data.get('update_existing', True)
        
        # Session ID oluştur (progress tracking için)
        self.session_id = str(uuid.uuid4())
        
        try:
            # Dosyayı geçici olarak kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Excel manager ile import
            excel_manager = CustomerExcelManager()
            results = excel_manager.import_customers_excel(
                tmp_file_path,
                update_existing=update_existing
            )
            
            # Sonuçları cache'e kaydet
            cache.set(f'import_results_{self.session_id}', results, 3600)
            
            # Başarı mesajı
            messages.success(
                self.request,
                f"{results['created']} müşteri oluşturuldu, {results['updated']} müşteri güncellendi."
            )
            
            if results['error_count'] > 0:
                messages.warning(
                    self.request,
                    f"{results['error_count']} satırda hata oluştu."
                )
            
            # Sonuç sayfasına yönlendir
            return redirect(self.get_success_url())
            
        except ExcelError as e:
            messages.error(self.request, f'Excel hatası: {str(e)}')
            return redirect('customers:excel-import')
        except Exception as e:
            logger.error(f'Import hatası: {str(e)}')
            messages.error(self.request, 'Beklenmeyen bir hata oluştu.')
            return redirect('customers:excel-import')
        finally:
            # Geçici dosyayı sil
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass


class AddressExcelImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView, CustomerExcelView):
    """Adres Excel import view'ı"""
    template_name = 'customers/address_excel_import.html'
    form_class = AddressExcelImportForm
    permission_required = 'customers.add_address'
    success_url = None
    
    def get_success_url(self):
        """Import sonuçları sayfasına yönlendir"""
        return reverse('customers:address-excel-import-results', 
                      kwargs={'session_id': self.session_id})
    
    def form_valid(self, form):
        """Excel dosyasını yükle ve import et"""
        excel_file = form.cleaned_data['excel_file']
        update_existing = form.cleaned_data.get('update_existing', True)
        
        # Session ID oluştur (progress tracking için)
        self.session_id = str(uuid.uuid4())
        
        try:
            # Dosyayı geçici olarak kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Excel manager ile import
            excel_manager = CustomerExcelManager()
            results = excel_manager.import_addresses_excel(
                tmp_file_path,
                update_existing=update_existing
            )
            
            # Sonuçları cache'e kaydet
            cache.set(f'import_results_{self.session_id}', results, 3600)
            
            # Başarı mesajı
            messages.success(
                self.request,
                f"{results['created']} adres oluşturuldu, {results['updated']} adres güncellendi."
            )
            
            if results['error_count'] > 0:
                messages.warning(
                    self.request,
                    f"{results['error_count']} satırda hata oluştu."
                )
            
            # Sonuç sayfasına yönlendir
            return redirect(self.get_success_url())
            
        except ExcelError as e:
            messages.error(self.request, f'Excel hatası: {str(e)}')
            return redirect('customers:address-excel-import')
        except Exception as e:
            logger.error(f'Import hatası: {str(e)}')
            messages.error(self.request, 'Beklenmeyen bir hata oluştu.')
            return redirect('customers:address-excel-import')
        finally:
            # Geçici dosyayı sil
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass


class ExcelImportResultsView(LoginRequiredMixin, TemplateView):
    """Import sonuçlarını göster"""
    template_name = 'customers/excel_import_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get('session_id')
        
        # Cache'den sonuçları al
        results = cache.get(f'import_results_{session_id}')
        
        if not results:
            context['error'] = 'Sonuçlar bulunamadı veya süresi doldu.'
        else:
            context['results'] = results
            context['statistics'] = CustomerExcelManager().get_import_statistics(results)
            context['session_id'] = session_id
        
        return context


class CustomerExcelExportView(LoginRequiredMixin, PermissionRequiredMixin, View, CustomerExcelView):
    """Müşterileri Excel'e export et"""
    permission_required = 'customers.view_customer'
    
    def get(self, request, *args, **kwargs):
        try:
            # Filtre parametrelerini al
            filter_form = CustomerFilterForm(request.GET)
            queryset = self._get_filtered_queryset(filter_form)
            
            # Export formatını al
            export_format = request.GET.get('format', 'excel')
            
            # Excel manager ile export
            excel_manager = CustomerExcelManager()
            
            if export_format == 'csv':
                content = excel_manager.export_customers_csv(queryset)
                content_type = 'text/csv'
                filename = f'musteriler_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
            else:
                content = excel_manager.export_customers_excel(queryset)
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = f'musteriler_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            
            # Response oluştur
            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f'Export hatası: {str(e)}')
            messages.error(request, 'Export sırasında bir hata oluştu.')
            return redirect('customers:customer-list')
    
    def _get_filtered_queryset(self, filter_form):
        """Form'a göre queryset filtrele"""
        queryset = Customer.objects.all()
        
        if filter_form.is_valid():
            # Müşteri tipi
            if filter_form.cleaned_data.get('type'):
                queryset = queryset.filter(type=filter_form.cleaned_data['type'])
                
            # Durum
            if filter_form.cleaned_data.get('is_active') is not None:
                queryset = queryset.filter(is_active=filter_form.cleaned_data['is_active'])
                
            # Arama
            if filter_form.cleaned_data.get('search'):
                search_term = filter_form.cleaned_data['search']
                queryset = queryset.filter(
                    models.Q(name__icontains=search_term) |
                    models.Q(company_name__icontains=search_term) |
                    models.Q(email__icontains=search_term) |
                    models.Q(phone__icontains=search_term)
                )
        
        return queryset


class AddressExcelExportView(LoginRequiredMixin, PermissionRequiredMixin, View, CustomerExcelView):
    """Adresleri Excel'e export et"""
    permission_required = 'customers.view_address'
    
    def get(self, request, *args, **kwargs):
        try:
            # Müşteri filtresi
            customer_id = request.GET.get('customer')
            if customer_id:
                queryset = Address.objects.filter(customer_id=customer_id)
            else:
                queryset = Address.objects.all()
            
            # Excel manager ile export
            excel_manager = CustomerExcelManager()
            content = excel_manager.export_addresses_excel(queryset)
            
            # Response oluştur
            filename = f'adresler_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            response = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f'Export hatası: {str(e)}')
            messages.error(request, 'Export sırasında bir hata oluştu.')
            return redirect('customers:customer-list')


class CustomerExcelTemplateView(LoginRequiredMixin, View, CustomerExcelView):
    """Müşteri import için boş Excel template indir"""
    
    def get(self, request, *args, **kwargs):
        try:
            excel_manager = CustomerExcelManager()
            template_content = excel_manager.generate_customer_import_template()
            
            response = HttpResponse(
                template_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            filename = f'musteri_import_template_{timezone.now().strftime("%Y%m%d")}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f'Template oluşturma hatası: {str(e)}')
            messages.error(request, 'Template oluşturulurken bir hata oluştu.')
            return redirect('customers:excel-import')


class AddressExcelTemplateView(LoginRequiredMixin, View, CustomerExcelView):
    """Adres import için boş Excel template indir"""
    
    def get(self, request, *args, **kwargs):
        try:
            excel_manager = CustomerExcelManager()
            template_content = excel_manager.generate_address_import_template()
            
            response = HttpResponse(
                template_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            filename = f'adres_import_template_{timezone.now().strftime("%Y%m%d")}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f'Template oluşturma hatası: {str(e)}')
            messages.error(request, 'Template oluşturulurken bir hata oluştu.')
            return redirect('customers:address-excel-import')


# Function-based views (geriye uyumluluk için)
@login_required
@permission_required('customers.add_customer')
def customer_excel_import_view(request):
    """Müşteri import için function-based view"""
    view = CustomerExcelImportView.as_view()
    return view(request)


@login_required
@permission_required('customers.add_address')
def address_excel_import_view(request):
    """Adres import için function-based view"""
    view = AddressExcelImportView.as_view()
    return view(request)


@login_required
def excel_import_results_view(request, session_id):
    """Import sonuçları için function-based view"""
    view = ExcelImportResultsView.as_view()
    return view(request, session_id=session_id)


@login_required
@permission_required('customers.view_customer')
def customer_excel_export_view(request):
    """Müşteri export için function-based view"""
    view = CustomerExcelExportView.as_view()
    return view(request)


@login_required
@permission_required('customers.view_address')
def address_excel_export_view(request):
    """Adres export için function-based view"""
    view = AddressExcelExportView.as_view()
    return view(request)


@login_required
def customer_excel_template_view(request):
    """Müşteri import template için function-based view"""
    view = CustomerExcelTemplateView.as_view()
    return view(request)


@login_required
def address_excel_template_view(request):
    """Adres import template için function-based view"""
    view = AddressExcelTemplateView.as_view()
    return view(request)


@login_required
@require_POST
def validate_excel_file(request):
    """Excel dosyasını import öncesi doğrula (AJAX)"""
    if 'excel_file' not in request.FILES:
        return JsonResponse({'error': 'Dosya bulunamadı'}, status=400)
    
    excel_file = request.FILES['excel_file']
    file_type = request.POST.get('type', 'customer')  # customer veya address
    
    try:
        # Dosyayı geçici olarak kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            for chunk in excel_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        # Excel dosyasını oku
        import pandas as pd
        df = pd.read_excel(tmp_file_path)
        
        # Gerekli sütunları kontrol et
        if file_type == 'customer':
            required_columns = ['Müşteri Adı *', 'Email *', 'Telefon *']
        else:  # address
            required_columns = ['Müşteri Email *', 'Adres Başlığı *', 'Adres Satırı 1 *', 'Şehir *']
            
        available_columns = df.columns.tolist()
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        # Sonuç oluştur
        validation_result = {
            'valid': len(missing_columns) == 0,
            'total_rows': len(df),
            'file_size': os.path.getsize(tmp_file_path),
        }
        
        if missing_columns:
            validation_result['errors'] = [f"Eksik sütunlar: {', '.join(missing_columns)}"]
        
        return JsonResponse(validation_result)
        
    except Exception as e:
        logger.error(f'Validasyon hatası: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        # Geçici dosyayı sil
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass