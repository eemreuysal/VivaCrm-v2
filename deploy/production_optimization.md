# VivaCRM v2 Production Optimizasyonları

## 1. Gunicorn Yapılandırması

```python
# gunicorn_config.py
import multiprocessing
import os

# Worker ayarları
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'  # Async worker
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout ayarları
timeout = 300
graceful_timeout = 30
keepalive = 5

# Binding
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Logging
accesslog = '/var/log/vivacrm/gunicorn-access.log'
errorlog = '/var/log/vivacrm/gunicorn-error.log'
loglevel = 'info'

# Process naming
proc_name = 'vivacrm'

# Stats
statsd_host = 'localhost:8125'
statsd_prefix = 'vivacrm'

# Preload
preload_app = True

# Enable thread option
threads = 4

# Connection recycling
max_requests = 5000
max_requests_jitter = 500
```

## 2. Nginx Yapılandırması

```nginx
# /etc/nginx/sites-available/vivacrm
upstream vivacrm {
    server 127.0.0.1:8000 fail_timeout=0;
    keepalive 32;
}

server {
    listen 80;
    server_name vivacrm.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name vivacrm.com;
    
    # SSL ayarları
    ssl_certificate /etc/ssl/certs/vivacrm.crt;
    ssl_certificate_key /etc/ssl/private/vivacrm.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE:ECDH:AES:HIGH:!NULL:!aNULL:!MD5:!ADH:!RC4;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:50m;
    ssl_session_timeout 1h;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Client body size
    client_max_body_size 100M;
    
    # Timeouts
    client_body_timeout 60;
    client_header_timeout 60;
    keepalive_timeout 65;
    send_timeout 60;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;
    limit_req zone=one burst=20 nodelay;
    
    # Static files
    location /static/ {
        alias /var/www/vivacrm/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    location /media/ {
        alias /var/www/vivacrm/media/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
    }
    
    # Django app
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_redirect off;
        proxy_buffering off;
        
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        proxy_pass http://vivacrm;
        
        # Proxy timeouts
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Health check
    location /health/ {
        access_log off;
        proxy_pass http://vivacrm;
    }
    
    # Monitoring endpoints
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

## 3. PostgreSQL Optimizasyonları

```sql
-- postgresql.conf optimizasyonları

# Bellek ayarları
shared_buffers = 256MB          # RAM'in %25'i
effective_cache_size = 1GB      # RAM'in %75'i
work_mem = 4MB                  # Sorgu başına bellek
maintenance_work_mem = 64MB     # Maintenance işlemleri için

# Checkpoint ayarları
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
max_wal_size = 1GB
min_wal_size = 80MB

# Bağlantı ayarları
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

# Query planner ayarları
random_page_cost = 1.1          # SSD için
effective_io_concurrency = 200  # SSD için
default_statistics_target = 100

# Loglama
log_min_duration_statement = 500ms
log_line_prefix = '%t [%p-%l] %q%u@%d '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0

-- İndexleme stratejisi
CREATE INDEX idx_orders_customer_status ON orders_order(customer_id, status);
CREATE INDEX idx_orders_created_at ON orders_order(created_at DESC);
CREATE INDEX idx_products_category_active ON products_product(category_id) WHERE is_active = true;
CREATE INDEX idx_customers_email ON customers_customer(email);
CREATE INDEX idx_orderitems_order_product ON orders_orderitem(order_id, product_id);

-- Vacuum ve analyze
ALTER TABLE orders_order SET (autovacuum_vacuum_scale_factor = 0.01);
ALTER TABLE products_product SET (autovacuum_analyze_scale_factor = 0.01);
```

## 4. Redis Optimizasyonları

```bash
# redis.conf

# Bellek limiti
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1      # 15 dakikada 1 değişiklik
save 300 10     # 5 dakikada 10 değişiklik
save 60 10000   # 1 dakikada 10000 değişiklik

# AOF
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no

# Performans
tcp-keepalive 60
timeout 300

# Security
requirepass your_strong_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""
```

## 5. Celery Optimizasyonları

```python
# celery_production.py
import os
from celery import Celery
from kombu import Queue, Exchange

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('vivacrm')

# Broker ve backend
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/1'

# Task serialization
app.conf.task_serializer = 'msgpack'
app.conf.result_serializer = 'msgpack'
app.conf.accept_content = ['msgpack', 'json']

# Timezone
app.conf.timezone = 'Europe/Istanbul'

# Task execution
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_time_limit = 300  # 5 dakika
app.conf.task_soft_time_limit = 270  # 4.5 dakika

# Worker settings
app.conf.worker_prefetch_multiplier = 2
app.conf.worker_max_tasks_per_child = 1000
app.conf.worker_disable_rate_limits = False

# Queue configuration
default_exchange = Exchange('default', type='direct')
priority_exchange = Exchange('priority', type='direct')

app.conf.task_queues = (
    Queue('default', default_exchange, routing_key='default'),
    Queue('priority', priority_exchange, routing_key='priority'),
    Queue('emails', default_exchange, routing_key='emails'),
    Queue('reports', default_exchange, routing_key='reports'),
)

# Task routing
app.conf.task_routes = {
    'send_email': {'queue': 'emails'},
    'generate_report': {'queue': 'reports'},
    'critical_task': {'queue': 'priority'},
}

# Beat schedule
app.conf.beat_schedule = {
    'cleanup-old-sessions': {
        'task': 'core.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=2, minute=0),  # Her gün saat 2:00
    },
    'generate-daily-report': {
        'task': 'reports.tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),  # Her gün gece yarısı
    },
    'update-cache': {
        'task': 'core.tasks.update_cache',
        'schedule': 300.0,  # Her 5 dakikada
    },
}
```

## 6. Docker Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    image: vivacrm:latest
    container_name: vivacrm_web
    restart: always
    volumes:
      - ./staticfiles:/app/staticfiles
      - ./media:/app/media
      - ./logs:/app/logs
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.production
      - DATABASE_URL=postgres://user:pass@db:5432/vivacrm
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    networks:
      - vivacrm_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: vivacrm_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./staticfiles:/var/www/static
      - ./media:/var/www/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    networks:
      - vivacrm_network

  db:
    image: postgres:15-alpine
    container_name: vivacrm_db
    restart: always
    environment:
      - POSTGRES_DB=vivacrm
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
    networks:
      - vivacrm_network
    command: postgres -c config_file=/etc/postgresql/postgresql.conf

  redis:
    image: redis:7-alpine
    container_name: vivacrm_redis
    restart: always
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    networks:
      - vivacrm_network
    command: redis-server /usr/local/etc/redis/redis.conf

  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: vivacrm_celery
    restart: always
    command: celery -A core worker -l info -Q default,priority,emails,reports
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.production
      - DATABASE_URL=postgres://user:pass@db:5432/vivacrm
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    networks:
      - vivacrm_network

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: vivacrm_beat
    restart: always
    command: celery -A core beat -l info
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings.production
      - DATABASE_URL=postgres://user:pass@db:5432/vivacrm
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    networks:
      - vivacrm_network

volumes:
  postgres_data:
  redis_data:

networks:
  vivacrm_network:
    driver: bridge
```

## 7. Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    networks:
      - monitoring

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: postgres-exporter
    environment:
      - DATA_SOURCE_NAME=postgresql://user:pass@db:5432/vivacrm?sslmode=disable
    ports:
      - "9187:9187"
    networks:
      - monitoring

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis-exporter
    environment:
      - REDIS_ADDR=redis://redis:6379
    ports:
      - "9121:9121"
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    external: true
```

## 8. Deployment Checklist

### Pre-deployment
- [ ] Tüm testler başarılı
- [ ] Security scan tamamlandı
- [ ] Database migration'lar hazır
- [ ] Static dosyalar collected
- [ ] Environment değişkenleri ayarlandı
- [ ] SSL sertifikası hazır
- [ ] Backup stratejisi belirlendi

### Deployment
- [ ] Database migration çalıştırıldı
- [ ] Static dosyalar yüklendi
- [ ] Cache temizlendi
- [ ] Celery worker'lar başlatıldı
- [ ] Health check'ler çalışıyor

### Post-deployment
- [ ] Monitoring aktif
- [ ] Log aggregation çalışıyor
- [ ] Backup'lar alınıyor
- [ ] Performance metrikleri normal
- [ ] Security scan'ler planlandı