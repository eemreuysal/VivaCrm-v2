# Dashboard Module

The Dashboard module provides visualization and reporting functionality for VivaCRM v2. It displays key business metrics, charts, and statistics for monitoring business performance.

## Architecture

The dashboard uses a modular architecture with the following components:

1. **View Layer**: Django views that render the dashboard templates
2. **API Layer**: REST API endpoints that provide data for the dashboard
3. **Cache Layer**: Redis-based caching system for performance optimization
4. **Task Layer**: Celery tasks for background processing and cache management

## Key Components

### Templates

- `dashboard.html`: Main dashboard template
- Partial templates in `partials/` directory:
  - `_dashboard_charts.html`: Chart components
  - `_dashboard_content.html`: Main content area
  - `_dashboard_filters.html`: Period filter controls
  - `_dashboard_orders.html`: Recent orders section
  - `_dashboard_stats.html`: Statistics cards
  - `_dashboard_stock.html`: Low stock products section

### JavaScript Components

- `dashboard.js`: Main dashboard initialization
- `dashboard-components.js`: Alpine.js components for dashboard UI

### Backend Components

- `views.py`: Main view logic and data preparation
- `api/views.py`: API endpoints for dashboard data
- `cache_helpers.py`: Caching utilities
- `tasks.py`: Celery tasks for background processing
- `signals.py`: Signal handlers for real-time data updates

## Caching Strategy

The dashboard implements a sophisticated caching strategy to optimize performance:

1. **Time-Based Caching**: Data is cached for specific time periods (day, week, month, year)
2. **Automatic Refresh**: Cached data is periodically refreshed by background tasks
3. **Cache Invalidation**: When related data changes, specific caches are invalidated
4. **Custom Cache Keys**: Unique cache keys based on parameters like time period

## Celery Tasks

The following Celery tasks are implemented for dashboard management:

1. `refresh_dashboard_data`: Refreshes commonly used dashboard caches (hourly)
2. `clean_old_dashboard_caches`: Cleans up accumulated cache keys (daily)
3. `update_dashboard_on_data_change`: Updates specific caches when models change
4. `generate_dashboard_cache_data`: Pre-generates all dashboard cache data (daily)
5. `monitor_dashboard_performance`: Monitors dashboard endpoint performance

## Signals

Signal handlers are implemented to automatically update dashboard data when related models change:

- `product_change_handler`: Updates product-related dashboard data
- `stock_movement_change_handler`: Updates stock-related dashboard data
- `order_change_handler`: Updates sales and order-related dashboard data
- `customer_change_handler`: Updates customer-related dashboard data
- `invoice_change_handler`: Updates financial dashboard data

## Performance Optimizations

The dashboard implements various performance optimizations:

1. **Query Optimization**: Optimized database queries with proper indexes
2. **Data Prefetching**: Related objects are prefetched to reduce database hits
3. **Caching Strategy**: Multi-level caching with proper invalidation
4. **Lazy Loading**: UI components load data only when needed
5. **Background Processing**: Resource-intensive operations run in background tasks

## Usage

### Viewing the Dashboard

The dashboard is available at `/dashboard/` and requires authentication.

### Filtering Data

- Time period filters: day, week, month, year, custom
- Data is automatically updated when filters change

### API Endpoints

- `/dashboard/api/chart-data/`: Provides chart data
- `/dashboard/api/stats/`: Provides statistical data
- `/dashboard/api/low-stock/`: Provides low stock products

## Testing

Tests are available in the `tests/` directory:

- `test_cache_helpers.py`: Tests for caching utilities
- `test_tasks.py`: Tests for Celery tasks

Run tests with:
```
python manage.py test dashboard
```

## Development

When extending the dashboard:

1. Follow the existing architecture and patterns
2. Use the provided caching utilities
3. Update signal handlers for new models
4. Add appropriate tests
5. Document changes in this README