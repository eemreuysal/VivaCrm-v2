#!/bin/bash

# Development Ortamı Başlatma Script'i

echo "🚀 VivaCRM Development Ortamı Başlatılıyor..."

# Ortam değişkenlerini ayarla
export DJANGO_ENV=development
echo "✅ Django ortamı: $DJANGO_ENV"

# Redis kontrolü
echo "🔍 Redis durumu kontrol ediliyor..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis çalışıyor"
else
    echo "⚠️  Redis çalışmıyor. Başlatılıyor..."
    redis-server --daemonize yes
fi

# PostgreSQL kontrolü (opsiyonel - SQLite kullanıyoruz)
# echo "🔍 PostgreSQL durumu kontrol ediliyor..."
# pg_isready

# NPM dependencies kontrolü
echo "📦 NPM bağımlılıkları kontrol ediliyor..."
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules bulunamadı. Yükleniyor..."
    npm install
fi

# CSS build
echo "🎨 CSS build ediliyor..."
npm run build:css

# Django migration kontrolü
echo "🗃️  Migration'lar kontrol ediliyor..."
python manage.py showmigrations | grep "\[ \]" > /dev/null
if [ $? -eq 0 ]; then
    echo "⚠️  Uygulanmamış migration'lar var. Uygulanıyor..."
    python manage.py migrate
else
    echo "✅ Tüm migration'lar uygulanmış"
fi

# Static dosyaları topla
echo "📁 Static dosyalar toplanıyor..."
python manage.py collectstatic --noinput

# CSS watch modunu başlat (arka planda)
echo "👁️  CSS watch modu başlatılıyor..."
npm run watch:css &

# Django sunucusunu başlat
echo "🌐 Django development sunucusu başlatılıyor..."
echo "=================================="
echo "Sunucu: http://localhost:8000"
echo "Admin: http://localhost:8000/admin"
echo "=================================="
python manage.py runserver