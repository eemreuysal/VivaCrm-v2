"""
Import result views for orders
"""
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from core.models_import import ImportTask, DetailedImportResult


class ImportTaskDetailView(LoginRequiredMixin, DetailView):
    """View for showing import task details and results"""
    model = ImportTask
    template_name = 'orders/import_task_detail.html'
    context_object_name = 'import_task'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get detailed results
        results = DetailedImportResult.objects.filter(
            import_task=self.object
        ).order_by('row_number')
        
        # Group by status
        context['results_by_status'] = {
            'created': results.filter(status='created'),
            'updated': results.filter(status='updated'),
            'failed': results.filter(status='failed'),
            'skipped': results.filter(status='skipped'),
        }
        
        # Get summary
        if hasattr(self.object, 'summary'):
            context['summary'] = self.object.summary
        
        return context


class ImportTaskListView(LoginRequiredMixin, ListView):
    """View for listing all import tasks"""
    model = ImportTask
    template_name = 'orders/import_task_list.html'
    context_object_name = 'import_tasks'
    paginate_by = 20
    
    def get_queryset(self):
        return ImportTask.objects.filter(
            type='order'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics
        queryset = self.get_queryset()
        context['total_imports'] = queryset.count()
        context['successful_imports'] = queryset.filter(status='completed').count()
        context['failed_imports'] = queryset.filter(status='failed').count()
        context['partial_imports'] = queryset.filter(status='partial').count()
        
        return context