#!/bin/bash
# Redis kurulum ve başlatma scripti

echo "Redis kurulumu ve başlatma işlemi..."

# macOS için Redis kurulumu
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS tespit edildi..."
    
    # Homebrew kontrolü
    if ! command -v brew &> /dev/null; then
        echo "Homebrew yüklü değil. Lütfen önce Homebrew yükleyin."
        exit 1
    fi
    
    # Redis kurulumu
    if ! command -v redis-server &> /dev/null; then
        echo "Redis kuruluyor..."
        brew install redis
    else
        echo "Redis zaten yüklü."
    fi
    
    # Redis hizmetini başlat
    echo "Redis hizmeti başlatılıyor..."
    brew services start redis
    
    # Redis durumunu kontrol et
    brew services list | grep redis
    
# Linux için Redis kurulumu
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux tespit edildi..."
    
    # Redis kurulumu (Ubuntu/Debian)
    if ! command -v redis-server &> /dev/null; then
        echo "Redis kuruluyor..."
        sudo apt-get update
        sudo apt-get install -y redis-server
    else
        echo "Redis zaten yüklü."
    fi
    
    # Redis hizmetini başlat
    echo "Redis hizmeti başlatılıyor..."
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Redis durumunu kontrol et
    sudo systemctl status redis-server
fi

# Redis bağlantısını test et
echo -e "\nRedis bağlantısı test ediliyor..."
redis-cli ping

# Redis versiyonunu göster
echo -e "\nRedis versiyonu:"
redis-cli --version

# Redis bilgilerini göster
echo -e "\nRedis server bilgileri:"
redis-cli INFO server | head -n 10

echo -e "\n✅ Redis kurulumu ve başlatma işlemi tamamlandı!"
echo "Django test scriptini çalıştırmak için: python test_redis_connection.py"