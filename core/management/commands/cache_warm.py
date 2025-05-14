"""
Management command to warm the cache.
"""
import time
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import importlib

# Set up logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Warm the cache by pre-populating common queries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--items',
            dest='items',
            default=100,
            type=int,
            help='Number of items to pre-cache for each model'
        )
        
        parser.add_argument(
            '--skip-models',
            dest='skip_models',
            nargs='+',
            help='Models to skip (format: app_label.model_name)'
        )
        
        parser.add_argument(
            '--only-models',
            dest='only_models',
            nargs='+',
            help='Only warm cache for these models (format: app_label.model_name)'
        )
        
        parser.add_argument(
            '--workers',
            dest='workers',
            default=4,
            type=int,
            help='Number of worker threads'
        )
    
    def handle(self, *args, **options):
        # Start timing
        start_time = time.time()
        
        # Get options
        items_count = options['items']
        skip_models = options['skip_models'] or []
        only_models = options['only_models'] or []
        workers = options['workers']
        
        # Log start
        self.stdout.write(self.style.SUCCESS(f"Starting cache warming..."))
        
        # Get cacheable models and views
        models_to_warm = self._get_models_to_warm(skip_models, only_models)
        viewsets_to_warm = self._get_viewsets_to_warm()
        
        # Warm up models
        self._warm_models(models_to_warm, items_count, workers)
        
        # Warm up viewsets
        self._warm_viewsets(viewsets_to_warm, items_count)
        
        # Get dashboard data
        self._warm_dashboard_data()
        
        # Log finish
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f"Cache warming completed in {elapsed_time:.2f} seconds"
        ))
    
    def _get_models_to_warm(self, skip_models, only_models):
        """
        Get a list of models to warm.
        """
        from django.apps import apps
        
        # Get all installed models
        all_models = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                model_label = f"{model._meta.app_label}.{model._meta.model_name}"
                
                # Skip certain models
                if model_label in skip_models:
                    continue
                
                # Only include specified models if provided
                if only_models and model_label not in only_models:
                    continue
                
                # Skip abstract models and models in excluded apps
                if model._meta.abstract or model._meta.app_label in [
                    'admin', 'contenttypes', 'sessions', 'auth'
                ]:
                    continue
                
                all_models.append(model)
        
        return all_models
    
    def _get_viewsets_to_warm(self):
        """
        Get a list of viewsets to warm.
        """
        viewsets = []
        
        # Try to import API router
        try:
            from rest_framework.routers import SimpleRouter
            from core.api_router import router as app_router
            
            # Get all registered viewsets
            for route in app_router.registry:
                prefix, viewset, basename = route
                viewsets.append((prefix, viewset))
        
        except (ImportError, AttributeError):
            logger.warning("Could not import API router, skipping viewset warming")
        
        return viewsets
    
    def _warm_models(self, models, items_count, workers):
        """
        Warm the cache for models.
        """
        self.stdout.write(f"Warming cache for {len(models)} models...")
        
        # Create tasks for each model
        tasks = []
        for model in models:
            model_label = f"{model._meta.app_label}.{model._meta.model_name}"
            tasks.append((model_label, model, items_count))
        
        # Use ThreadPoolExecutor to warm in parallel
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._warm_model, label, model, count): label
                for label, model, count in tasks
            }
            
            for future in as_completed(futures):
                label = futures[future]
                try:
                    count = future.result()
                    self.stdout.write(f"  Warmed {count} items for {label}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"  Error warming {label}: {str(e)}"
                    ))
    
    def _warm_model(self, label, model, count):
        """
        Warm the cache for a specific model.
        """
        # Get queryset
        queryset = model.objects.all()
        
        # Annotate with count if possible
        try:
            if hasattr(model, 'created_at'):
                queryset = queryset.order_by('-created_at')
            elif hasattr(model, 'id'):
                queryset = queryset.order_by('-id')
        except Exception:
            pass
        
        # Limit to count
        queryset = queryset[:count]
        
        # Fetch all items
        items = list(queryset)
        
        # Try to call common methods on each item to warm method cache
        for item in items:
            try:
                # Cache common properties
                str(item)
                if hasattr(item, 'get_absolute_url'):
                    item.get_absolute_url()
                
                # Cache calculated fields
                for field in dir(item):
                    if field.startswith('get_') and field.endswith('_display'):
                        try:
                            getattr(item, field)()
                        except (TypeError, ValueError, AttributeError):
                            pass
            except Exception:
                continue
        
        return len(items)
    
    def _warm_viewsets(self, viewsets, items_count):
        """
        Warm the cache for viewsets.
        """
        if not viewsets:
            return
        
        self.stdout.write(f"Warming cache for {len(viewsets)} viewsets...")
        
        # Process each viewset
        for prefix, viewset_class in viewsets:
            try:
                # Create viewset instance
                viewset = viewset_class()
                
                # Get queryset
                queryset = viewset.get_queryset()
                
                # Limit to count
                queryset = queryset[:items_count]
                
                # Fetch all items
                items = list(queryset)
                
                self.stdout.write(f"  Warmed {len(items)} items for {prefix} viewset")
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"  Error warming {prefix} viewset: {str(e)}"
                ))
    
    def _warm_dashboard_data(self):
        """
        Warm the cache for dashboard data.
        """
        self.stdout.write("Warming dashboard data...")
        
        try:
            # Try to import dashboard data functions
            from dashboard.views import get_dashboard_data
            
            # Call the function to cache its result
            get_dashboard_data()
            
            self.stdout.write("  Warmed dashboard data")
        
        except (ImportError, AttributeError):
            self.stdout.write(self.style.WARNING(
                "  Could not import dashboard data functions, skipping"
            ))