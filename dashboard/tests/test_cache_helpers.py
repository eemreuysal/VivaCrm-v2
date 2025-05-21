"""
Tests for Dashboard cache helper functions.

These tests verify that dashboard cache helper functions work correctly
for caching and retrieving dashboard data.
"""

from unittest import mock

from django.test import TestCase
from django.core.cache import cache

from ..cache_helpers import (
    dashboard_stats_cache_key,
    chart_data_cache_key,
    low_stock_cache_key,
    get_cached_dashboard_stats,
    get_cached_chart_data,
    get_cached_low_stock_products,
    invalidate_dashboard_caches,
    refresh_dashboard_caches
)


class DashboardCacheHelpersTests(TestCase):
    """Tests for dashboard cache helper functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear cache before each test
        cache.clear()
    
    def test_dashboard_stats_cache_key(self):
        """Test dashboard_stats_cache_key function generates correct keys."""
        # Test with no dates
        key1 = dashboard_stats_cache_key()
        self.assertEqual(key1, 'dashboard:stats')
        
        # Test with start date only
        key2 = dashboard_stats_cache_key(start_date='2023-01-01')
        self.assertEqual(key2, 'dashboard:stats:start:2023-01-01')
        
        # Test with end date only
        key3 = dashboard_stats_cache_key(end_date='2023-01-31')
        self.assertEqual(key3, 'dashboard:stats:end:2023-01-31')
        
        # Test with both dates
        key4 = dashboard_stats_cache_key(start_date='2023-01-01', end_date='2023-01-31')
        self.assertEqual(key4, 'dashboard:stats:start:2023-01-01:end:2023-01-31')
    
    def test_chart_data_cache_key(self):
        """Test chart_data_cache_key function generates correct keys."""
        # Test with default period
        key1 = chart_data_cache_key('sales')
        self.assertEqual(key1, 'dashboard:chart:sales:month')
        
        # Test with custom period
        key2 = chart_data_cache_key('products', period='year')
        self.assertEqual(key2, 'dashboard:chart:products:year')
    
    def test_low_stock_cache_key(self):
        """Test low_stock_cache_key function generates correct keys."""
        # Test with no limit
        key1 = low_stock_cache_key()
        self.assertEqual(key1, 'dashboard:low_stock:all')
        
        # Test with limit
        key2 = low_stock_cache_key(limit=10)
        self.assertEqual(key2, 'dashboard:low_stock:10')
    
    @mock.patch('dashboard.cache_helpers.get_dashboard_data')
    def test_get_cached_dashboard_stats(self, mock_get_data):
        """Test get_cached_dashboard_stats function caches and retrieves data."""
        # Setup mock to return test data
        test_data = {'total_orders': 100, 'total_sales': 5000}
        mock_get_data.return_value = test_data
        
        # First call should compute data
        result1 = get_cached_dashboard_stats()
        
        # Verify mock was called
        mock_get_data.assert_called_once()
        
        # Verify result
        self.assertEqual(result1, test_data)
        
        # Reset mock to verify it's not called again
        mock_get_data.reset_mock()
        
        # Second call should retrieve from cache
        result2 = get_cached_dashboard_stats()
        
        # Verify mock was not called
        mock_get_data.assert_not_called()
        
        # Verify result is same as first call
        self.assertEqual(result2, test_data)
        
        # Test forced refresh
        mock_get_data.reset_mock()
        result3 = get_cached_dashboard_stats(refresh=True)
        
        # Verify mock was called again for refresh
        mock_get_data.assert_called_once()
        
        # Verify result is same
        self.assertEqual(result3, test_data)
    
    @mock.patch('dashboard.cache_helpers.get_chart_data')
    def test_get_cached_chart_data(self, mock_get_data):
        """Test get_cached_chart_data function caches and retrieves data."""
        # Setup mock to return test data
        test_data = {'labels': ['Jan', 'Feb'], 'data': [100, 200]}
        mock_get_data.return_value = test_data
        
        # First call should compute data
        result1 = get_cached_chart_data('sales', 'month')
        
        # Verify mock was called
        mock_get_data.assert_called_once_with('sales', 'month')
        
        # Verify result
        self.assertEqual(result1, test_data)
        
        # Reset mock to verify it's not called again
        mock_get_data.reset_mock()
        
        # Second call should retrieve from cache
        result2 = get_cached_chart_data('sales', 'month')
        
        # Verify mock was not called
        mock_get_data.assert_not_called()
        
        # Verify result is same as first call
        self.assertEqual(result2, test_data)
    
    @mock.patch('dashboard.cache_helpers.cache.keys')
    @mock.patch('dashboard.cache_helpers.cache.delete_many')
    def test_invalidate_dashboard_caches(self, mock_delete_many, mock_keys):
        """Test invalidate_dashboard_caches function clears all dashboard caches."""
        # Setup mock to return test keys
        test_keys = ['dashboard:stats', 'dashboard:chart:sales:month']
        mock_keys.return_value = test_keys
        
        # Call function
        invalidate_dashboard_caches()
        
        # Verify mock was called
        mock_keys.assert_called_once_with('dashboard:*')
        
        # Verify delete_many was called with the keys
        mock_delete_many.assert_called_once_with(test_keys)
        
        # Test with no keys
        mock_keys.reset_mock()
        mock_delete_many.reset_mock()
        mock_keys.return_value = []
        
        # Call function
        invalidate_dashboard_caches()
        
        # Verify mock was called
        mock_keys.assert_called_once_with('dashboard:*')
        
        # Verify delete_many was not called
        mock_delete_many.assert_not_called()
    
    @mock.patch('dashboard.cache_helpers.get_cached_dashboard_stats')
    @mock.patch('dashboard.cache_helpers.get_cached_chart_data')
    @mock.patch('dashboard.cache_helpers.get_cached_low_stock_products')
    def test_refresh_dashboard_caches(self, mock_low_stock, mock_chart_data, mock_stats):
        """Test refresh_dashboard_caches function refreshes all dashboard caches."""
        # Call function
        refresh_dashboard_caches()
        
        # Verify that get_cached_dashboard_stats was called with refresh=True
        mock_stats.assert_called_once_with(refresh=True)
        
        # Verify that get_cached_chart_data was called for each chart type and period
        self.assertEqual(mock_chart_data.call_count, 12)  # 3 chart types * 4 periods
        
        # Verify that get_cached_low_stock_products was called with refresh=True
        mock_low_stock.assert_called_once_with(refresh=True)