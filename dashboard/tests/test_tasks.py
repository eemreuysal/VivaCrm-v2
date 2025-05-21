"""
Tests for Dashboard Celery tasks.

These tests verify that dashboard Celery tasks function correctly for
cache management, data refresh, and performance monitoring.
"""

from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache

from ..tasks import (
    refresh_dashboard_data,
    clean_old_dashboard_caches,
    update_dashboard_on_data_change,
    generate_dashboard_cache_data,
    monitor_dashboard_performance
)


class DashboardTasksTests(TestCase):
    """Tests for the dashboard Celery tasks."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear cache before each test
        cache.clear()
    
    @mock.patch('dashboard.tasks.refresh_dashboard_caches')
    @mock.patch('dashboard.tasks.get_cached_low_stock_products')
    def test_refresh_dashboard_data(self, mock_low_stock, mock_refresh):
        """Test refresh_dashboard_data task."""
        # Execute the task
        result = refresh_dashboard_data()
        
        # Verify results
        self.assertTrue(result)
        
        # Verify that refresh_dashboard_caches was called for each period
        self.assertEqual(mock_refresh.call_count, 3)
        mock_refresh.assert_any_call(period='day')
        mock_refresh.assert_any_call(period='week')
        mock_refresh.assert_any_call(period='month')
        
        # Verify that get_cached_low_stock_products was called once
        mock_low_stock.assert_called_once_with(limit=20, threshold_ratio=1.0)
    
    @mock.patch('dashboard.tasks.invalidate_dashboard_caches')
    @mock.patch('dashboard.tasks.refresh_dashboard_data.delay')
    def test_clean_old_dashboard_caches(self, mock_refresh_task, mock_invalidate):
        """Test clean_old_dashboard_caches task."""
        # Execute the task
        result = clean_old_dashboard_caches()
        
        # Verify results
        self.assertTrue(result)
        
        # Verify that invalidate_dashboard_caches was called
        mock_invalidate.assert_called_once()
        
        # Verify that refresh_dashboard_data task was called
        mock_refresh_task.assert_called_once()
    
    @mock.patch('dashboard.tasks.invalidate_dashboard_caches')
    @mock.patch('dashboard.tasks.get_cached_low_stock_products')
    @mock.patch('dashboard.tasks.get_cached_chart_data')
    @mock.patch('dashboard.tasks.get_cached_dashboard_stats')
    def test_update_dashboard_on_data_change_order(self, mock_stats, mock_chart, mock_low_stock, mock_invalidate):
        """Test update_dashboard_on_data_change task with Order model."""
        # Execute the task for Order model
        result = update_dashboard_on_data_change('Order', 123)
        
        # Verify results
        self.assertTrue(result)
        
        # For Order model, invalidate_dashboard_caches should be called
        mock_invalidate.assert_called_once()
        
        # Other methods should not be called for Order model
        mock_stats.assert_not_called()
        mock_chart.assert_not_called()
        mock_low_stock.assert_not_called()
    
    @mock.patch('dashboard.tasks.invalidate_dashboard_caches')
    @mock.patch('dashboard.tasks.get_cached_low_stock_products')
    @mock.patch('dashboard.tasks.get_cached_chart_data')
    @mock.patch('dashboard.tasks.get_cached_dashboard_stats')
    def test_update_dashboard_on_data_change_product(self, mock_stats, mock_chart, mock_low_stock, mock_invalidate):
        """Test update_dashboard_on_data_change task with Product model."""
        # Execute the task for Product model
        result = update_dashboard_on_data_change('Product', 456)
        
        # Verify results
        self.assertTrue(result)
        
        # For Product model, specific caches should be refreshed
        mock_low_stock.assert_called_once_with(limit=20, refresh=True)
        mock_chart.assert_called_once_with('products', 'month', refresh=True)
        
        # These methods should not be called for Product model
        mock_invalidate.assert_not_called()
        mock_stats.assert_not_called()
    
    @mock.patch('dashboard.tasks.invalidate_dashboard_caches')
    @mock.patch('dashboard.tasks.get_cached_dashboard_stats')
    @mock.patch('dashboard.tasks.get_cached_chart_data')
    @mock.patch('dashboard.tasks.get_cached_low_stock_products')
    def test_generate_dashboard_cache_data(self, mock_low_stock, mock_chart, mock_stats, mock_invalidate):
        """Test generate_dashboard_cache_data task."""
        # Execute the task
        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime(2023, 5, 15, tzinfo=timezone.utc)
            result = generate_dashboard_cache_data()
        
        # Verify results
        self.assertTrue(result)
        
        # Verify that invalidate_dashboard_caches was called
        mock_invalidate.assert_called_once()
        
        # Verify that get_cached_dashboard_stats was called for standard periods
        self.assertEqual(mock_stats.call_count, 6)  # 4 standard periods + YTD + QTD
        
        # Verify that get_cached_chart_data was called for all chart types and periods
        self.assertEqual(mock_chart.call_count, 16)  # 4 chart types * 4 periods
        
        # Verify that get_cached_low_stock_products was called with different limits
        self.assertEqual(mock_low_stock.call_count, 3)
    
    @mock.patch('dashboard.tasks.get_endpoint_metrics')
    @mock.patch('dashboard.tasks.log_performance_alert')
    @mock.patch('dashboard.tasks.get_cached_dashboard_stats')
    def test_monitor_dashboard_performance(self, mock_stats, mock_log_alert, mock_get_metrics):
        """Test monitor_dashboard_performance task."""
        # Setup mock return values
        mock_get_metrics.return_value = {
            'avg_response_time': 600,  # Should trigger alert (> 500)
            'p95_response_time': 1200,  # Should trigger alert (> 1000)
            'error_rate': 0.06,  # Should trigger alert (> 0.05)
        }
        
        # Execute the task
        with mock.patch('django.db.connection.execute_wrapper'):
            result = monitor_dashboard_performance()
        
        # Verify results
        self.assertTrue(result)
        
        # Verify that get_endpoint_metrics was called for each endpoint
        self.assertEqual(mock_get_metrics.call_count, 5)
        
        # Verify that log_performance_alert was called for each alert condition
        self.assertEqual(mock_log_alert.call_count, 15)  # 3 alerts * 5 endpoints
        
        # Verify that get_cached_dashboard_stats was called
        mock_stats.assert_called_once_with(refresh=True)