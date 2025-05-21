"""
VivaCRM v2 Celery Task Optimizasyonları

Bu dosya, Celery task performansını artırmak için kullanılacak optimizasyonları içerir.
"""
import time
import functools
import logging
from typing import Any, Dict, List, Optional, Callable
from celery import Task, shared_task, group, chain, chord
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import json
import redis

logger = get_task_logger(__name__)


# 1. Optimized Task Base Class
class OptimizedTask(Task):
    """Optimize edilmiş task base class"""
    
    # Retry configuration
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    # Rate limiting
    rate_limit = '100/m'
    
    # Time limits
    soft_time_limit = 300  # 5 minutes
    time_limit = 600  # 10 minutes
    
    # Result caching
    cache_result = True
    cache_timeout = 3600  # 1 hour
    
    def __call__(self, *args, **kwargs):
        """Task execution with caching"""
        if self.cache_result:
            # Generate cache key
            cache_key = self._get_cache_key(args, kwargs)
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for task {self.name}")
                return cached_result
        
        # Execute task
        result = super().__call__(*args, **kwargs)
        
        # Cache result
        if self.cache_result and result is not None:
            cache.set(cache_key, result, self.cache_timeout)
        
        return result
    
    def _get_cache_key(self, args, kwargs):
        """Generate cache key for task"""
        import hashlib
        
        # Serialize arguments
        key_data = {
            'task': self.name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        
        # Hash
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"celery_cache:{self.name}:{key_hash}"
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(
            f"Task {self.name} failed with args {args}, kwargs {kwargs}: {exc}"
        )
        
        # Send notification for critical tasks
        if hasattr(self, 'critical') and self.critical:
            self._send_failure_notification(exc, task_id, args, kwargs)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {self.name} completed successfully")
        
        # Update metrics
        self._update_success_metrics()
    
    def _send_failure_notification(self, exc, task_id, args, kwargs):
        """Send failure notification"""
        # Implement notification logic (email, Slack, etc.)
        pass
    
    def _update_success_metrics(self):
        """Update success metrics"""
        # Implement metrics tracking
        pass


# 2. Task Result Caching
def cache_task_result(timeout=3600, key_prefix=None):
    """Decorator for caching task results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                logger.info(f"Cache hit for {func.__name__}")
                return result
            
            # Execute task
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                cache.set(cache_key, result, timeout)
            
            return result
        
        # Preserve task attributes
        wrapper.name = getattr(func, 'name', func.__name__)
        return wrapper
    return decorator


# 3. Batch Processing Tasks
class BatchProcessor:
    """Batch processing utility"""
    
    def __init__(self, batch_size=100, timeout=300):
        self.batch_size = batch_size
        self.timeout = timeout
        self.redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    
    def add_to_batch(self, batch_key, item):
        """Add item to batch"""
        self.redis_client.rpush(batch_key, json.dumps(item))
        self.redis_client.expire(batch_key, self.timeout)
    
    def get_batch(self, batch_key):
        """Get and clear batch"""
        pipe = self.redis_client.pipeline()
        pipe.lrange(batch_key, 0, self.batch_size - 1)
        pipe.ltrim(batch_key, self.batch_size, -1)
        results = pipe.execute()
        
        items = []
        for item in results[0]:
            items.append(json.loads(item))
        
        return items
    
    def process_batch(self, batch_key, processor_func):
        """Process a batch of items"""
        items = self.get_batch(batch_key)
        
        if items:
            return processor_func(items)
        
        return None


# 4. Task Chunking
@shared_task(base=OptimizedTask)
def process_large_dataset(dataset_id, chunk_size=1000):
    """Process large dataset in chunks"""
    from products.models import Product
    
    # Get total count
    total_count = Product.objects.filter(dataset_id=dataset_id).count()
    
    # Create chunks
    chunks = []
    for offset in range(0, total_count, chunk_size):
        chunks.append(
            process_chunk.s(dataset_id, offset, chunk_size)
        )
    
    # Execute chunks in parallel
    job = group(chunks)
    result = job.apply_async()
    
    # Wait for all chunks to complete
    results = result.get()
    
    # Combine results
    return combine_chunk_results(results)


@shared_task(base=OptimizedTask)
def process_chunk(dataset_id, offset, limit):
    """Process a single chunk"""
    from products.models import Product
    
    products = Product.objects.filter(
        dataset_id=dataset_id
    )[offset:offset+limit]
    
    results = []
    for product in products:
        # Process each product
        result = process_single_product(product)
        results.append(result)
    
    return results


def combine_chunk_results(chunk_results):
    """Combine results from all chunks"""
    combined = []
    for chunk in chunk_results:
        combined.extend(chunk)
    return combined


# 5. Priority Queue Management
class PriorityTaskRouter:
    """Route tasks to appropriate queues based on priority"""
    
    def route_for_task(self, task, args=None, kwargs=None, **options):
        """Route task to appropriate queue"""
        
        # High priority tasks
        high_priority_tasks = [
            'send_critical_email',
            'process_payment',
            'update_inventory'
        ]
        
        # Low priority tasks
        low_priority_tasks = [
            'generate_report',
            'cleanup_old_data',
            'sync_external_data'
        ]
        
        if task in high_priority_tasks:
            return {
                'queue': 'high_priority',
                'routing_key': 'high.priority',
                'priority': 9
            }
        elif task in low_priority_tasks:
            return {
                'queue': 'low_priority',
                'routing_key': 'low.priority',
                'priority': 1
            }
        else:
            return {
                'queue': 'default',
                'routing_key': 'default',
                'priority': 5
            }


# 6. Task Debouncing
class TaskDebouncer:
    """Debounce task execution"""
    
    def __init__(self, delay=5):
        self.delay = delay
        self.redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    
    def debounce(self, task_name, task_id, *args, **kwargs):
        """Debounce task execution"""
        # Create unique key
        key = f"debounce:{task_name}:{task_id}"
        
        # Check if task is already scheduled
        if self.redis_client.exists(key):
            # Cancel previous task
            self.cancel_task(key)
        
        # Schedule new task
        from celery import current_app
        task = current_app.tasks[task_name]
        
        # Apply with countdown
        result = task.apply_async(
            args=args,
            kwargs=kwargs,
            countdown=self.delay
        )
        
        # Store task ID
        self.redis_client.setex(key, self.delay + 10, result.id)
        
        return result
    
    def cancel_task(self, key):
        """Cancel a debounced task"""
        task_id = self.redis_client.get(key)
        if task_id:
            AsyncResult(task_id).revoke()


# 7. Task Monitoring
class TaskMonitor:
    """Monitor task execution"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    
    def track_task_start(self, task_id, task_name):
        """Track task start"""
        key = f"task_monitor:{task_id}"
        data = {
            'task_name': task_name,
            'started_at': datetime.now().isoformat(),
            'status': 'running'
        }
        self.redis_client.setex(key, 3600, json.dumps(data))
    
    def track_task_complete(self, task_id, result=None):
        """Track task completion"""
        key = f"task_monitor:{task_id}"
        data = json.loads(self.redis_client.get(key) or '{}')
        data.update({
            'completed_at': datetime.now().isoformat(),
            'status': 'completed',
            'duration': self._calculate_duration(data),
            'result_size': len(str(result)) if result else 0
        })
        self.redis_client.setex(key, 3600, json.dumps(data))
    
    def track_task_failure(self, task_id, exception):
        """Track task failure"""
        key = f"task_monitor:{task_id}"
        data = json.loads(self.redis_client.get(key) or '{}')
        data.update({
            'failed_at': datetime.now().isoformat(),
            'status': 'failed',
            'error': str(exception),
            'duration': self._calculate_duration(data)
        })
        self.redis_client.setex(key, 3600, json.dumps(data))
    
    def get_task_stats(self, task_name=None):
        """Get task statistics"""
        stats = {
            'total_tasks': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'avg_duration': 0
        }
        
        # Scan all task keys
        for key in self.redis_client.scan_iter("task_monitor:*"):
            data = json.loads(self.redis_client.get(key))
            
            if task_name and data.get('task_name') != task_name:
                continue
            
            stats['total_tasks'] += 1
            stats[data['status']] += 1
            
            if 'duration' in data:
                stats['avg_duration'] += data['duration']
        
        if stats['completed'] > 0:
            stats['avg_duration'] /= stats['completed']
        
        return stats
    
    def _calculate_duration(self, data):
        """Calculate task duration"""
        if 'started_at' not in data:
            return 0
        
        started = datetime.fromisoformat(data['started_at'])
        ended = datetime.now()
        
        return (ended - started).total_seconds()


# 8. Distributed Locking
class DistributedLock:
    """Distributed lock for Celery tasks"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis.from_url(
            settings.CELERY_BROKER_URL
        )
    
    def acquire_lock(self, lock_name, timeout=60):
        """Acquire distributed lock"""
        identifier = str(time.time())
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            if self.redis_client.set(
                lock_name, 
                identifier, 
                ex=timeout, 
                nx=True
            ):
                return identifier
            
            time.sleep(0.001)
        
        return None
    
    def release_lock(self, lock_name, identifier):
        """Release distributed lock"""
        pipe = self.redis_client.pipeline(True)
        
        while True:
            try:
                pipe.watch(lock_name)
                if pipe.get(lock_name) == identifier:
                    pipe.multi()
                    pipe.delete(lock_name)
                    pipe.execute()
                    return True
                
                pipe.unwatch()
                break
            except redis.WatchError:
                pass
        
        return False
    
    def with_lock(self, lock_name, timeout=60):
        """Decorator for locking tasks"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                identifier = self.acquire_lock(lock_name, timeout)
                if identifier:
                    try:
                        return func(*args, **kwargs)
                    finally:
                        self.release_lock(lock_name, identifier)
                else:
                    raise Exception(f"Could not acquire lock: {lock_name}")
            
            return wrapper
        return decorator


# 9. Task Pipeline
class TaskPipeline:
    """Create complex task pipelines"""
    
    @staticmethod
    def create_pipeline(tasks):
        """Create a pipeline of tasks"""
        if not tasks:
            return None
        
        # Create chain
        pipeline = chain(*tasks)
        return pipeline
    
    @staticmethod
    def create_parallel_pipeline(task_groups):
        """Create parallel pipeline"""
        groups = []
        
        for task_group in task_groups:
            if isinstance(task_group, list):
                groups.append(group(*task_group))
            else:
                groups.append(task_group)
        
        return chord(groups)
    
    @staticmethod
    def create_conditional_pipeline(condition_task, true_tasks, false_tasks):
        """Create conditional pipeline"""
        from celery import signature
        
        def conditional_router(result):
            if result:
                return chain(*true_tasks)
            else:
                return chain(*false_tasks)
        
        return chain(
            condition_task,
            signature(conditional_router)
        )


# 10. Example Optimized Tasks
@shared_task(base=OptimizedTask, bind=True)
@cache_task_result(timeout=3600)
def generate_sales_report(self, date_from, date_to):
    """Generate sales report with optimizations"""
    # Distributed lock to prevent duplicate reports
    lock = DistributedLock()
    lock_name = f"sales_report:{date_from}:{date_to}"
    
    identifier = lock.acquire_lock(lock_name, timeout=300)
    if not identifier:
        logger.warning("Another report generation is in progress")
        return None
    
    try:
        # Monitor task execution
        monitor = TaskMonitor()
        monitor.track_task_start(self.request.id, self.name)
        
        # Process in chunks
        from orders.models import Order
        
        # Get total count
        total_orders = Order.objects.filter(
            created_at__range=[date_from, date_to]
        ).count()
        
        # Process in chunks
        chunk_size = 1000
        results = []
        
        for offset in range(0, total_orders, chunk_size):
            chunk_result = process_report_chunk.delay(
                date_from, date_to, offset, chunk_size
            )
            results.append(chunk_result)
        
        # Wait for all chunks
        chunk_results = [r.get() for r in results]
        
        # Combine results
        final_report = combine_report_chunks(chunk_results)
        
        # Track completion
        monitor.track_task_complete(self.request.id, final_report)
        
        return final_report
        
    except Exception as e:
        monitor.track_task_failure(self.request.id, e)
        raise
    finally:
        lock.release_lock(lock_name, identifier)


@shared_task(base=OptimizedTask)
def process_report_chunk(date_from, date_to, offset, limit):
    """Process a chunk of the report"""
    from orders.models import Order
    from django.db.models import Sum, Count
    
    orders = Order.objects.filter(
        created_at__range=[date_from, date_to]
    )[offset:offset+limit]
    
    # Aggregate data
    chunk_data = orders.aggregate(
        total_revenue=Sum('total'),
        order_count=Count('id'),
        avg_order_value=Avg('total')
    )
    
    return chunk_data


def combine_report_chunks(chunks):
    """Combine report chunks"""
    combined = {
        'total_revenue': 0,
        'order_count': 0,
        'avg_order_value': 0
    }
    
    for chunk in chunks:
        combined['total_revenue'] += chunk['total_revenue'] or 0
        combined['order_count'] += chunk['order_count'] or 0
    
    if combined['order_count'] > 0:
        combined['avg_order_value'] = (
            combined['total_revenue'] / combined['order_count']
        )
    
    return combined


# 11. Task Health Check
@shared_task
def health_check():
    """Celery health check task"""
    return {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'worker': current_app.control.inspect().active()
    }