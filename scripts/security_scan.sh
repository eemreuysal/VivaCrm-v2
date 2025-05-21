#!/bin/bash

# VivaCRM v2 Güvenlik Tarama Betiği
# Bu betik, yaygın güvenlik açıklarını tespit etmek için çeşitli tarayıcıları çalıştırır.

echo "VivaCRM v2 Güvenlik Tarama Betiği"
echo "=================================="
echo

# Renk tanımlamaları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Sonuç dosyaları için klasör oluştur
REPORT_DIR="security/reports"
mkdir -p $REPORT_DIR
DATE=$(date +%Y-%m-%d-%H-%M)

# Bağımlılıkları kontrol et
check_dependency() {
    if ! command -v $1 &> /dev/null
    then
        echo -e "${RED}[HATA]${NC} $1 bulunamadı. Lütfen yükleyin."
        echo "Yükleme komutu: $2"
        return 1
    fi
    return 0
}

echo -e "${BLUE}Bağımlılıkları Kontrol Ediliyor...${NC}"
check_dependency "bandit" "pip install bandit" || exit 1
check_dependency "safety" "pip install safety" || exit 1
check_dependency "npm" "apt-get install npm" || npm --version >/dev/null || exit 1

# 1. Python bağımlılıklarını güvenlik açıkları için tarama
echo -e "\n${BLUE}1. Python Bağımlılıklarını Tarıyor...${NC}"
safety check -r requirements.txt --output text > $REPORT_DIR/safety-$DATE.txt 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[BAŞARILI]${NC} Python bağımlılıklarında güvenlik açığı bulunamadı."
else
    echo -e "${YELLOW}[UYARI]${NC} Python bağımlılıklarında potansiyel güvenlik açıkları bulundu."
    echo -e "Detaylar için: $REPORT_DIR/safety-$DATE.txt"
fi

# 2. Python kodunu statik analiz ile tarıyor
echo -e "\n${BLUE}2. Python Kodunu Güvenlik Açıkları İçin Tarıyor...${NC}"
bandit -r . -c security/bandit.yaml -f html -o $REPORT_DIR/bandit-$DATE.html
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[BAŞARILI]${NC} Python kodunda güvenlik açığı bulunamadı."
else
    echo -e "${YELLOW}[UYARI]${NC} Python kodunda potansiyel güvenlik açıkları bulundu."
    echo -e "Detaylar için: $REPORT_DIR/bandit-$DATE.html"
fi

# 3. JavaScript bağımlılıklarını tarıyor
if [ -f package.json ]; then
    echo -e "\n${BLUE}3. JavaScript Bağımlılıklarını Tarıyor...${NC}"
    npm audit --json > $REPORT_DIR/npm-audit-$DATE.json 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[BAŞARILI]${NC} JavaScript bağımlılıklarında güvenlik açığı bulunamadı."
    else
        echo -e "${YELLOW}[UYARI]${NC} JavaScript bağımlılıklarında potansiyel güvenlik açıkları bulundu."
        echo -e "Detaylar için: $REPORT_DIR/npm-audit-$DATE.json"
    fi
else
    echo -e "\n${BLUE}3. JavaScript Bağımlılıkları Taraması Atlanıyor...${NC}"
    echo -e "   package.json dosyası bulunamadı."
fi

# 4. Django güvenlik ayarlarını kontrol et
echo -e "\n${BLUE}4. Django Güvenlik Ayarlarını Kontrol Ediyor...${NC}"
python manage.py check --deploy > $REPORT_DIR/django-check-$DATE.txt 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[BAŞARILI]${NC} Django güvenlik ayarları uygun."
else
    echo -e "${YELLOW}[UYARI]${NC} Django güvenlik ayarlarında bazı sorunlar olabilir."
    echo -e "Detaylar için: $REPORT_DIR/django-check-$DATE.txt"
fi

# 5. Gizli anahtarları tara
echo -e "\n${BLUE}5. Git Repo'da Olası Gizli Anahtarlar Aranıyor...${NC}"
if check_dependency "trufflehog" "pip install trufflehog"; then
    trufflehog --regex --entropy=True . > $REPORT_DIR/secrets-$DATE.txt 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[BAŞARILI]${NC} Olası gizli anahtar bulunamadı."
    else
        echo -e "${YELLOW}[UYARI]${NC} Olası gizli anahtarlar bulundu."
        echo -e "Detaylar için: $REPORT_DIR/secrets-$DATE.txt"
    fi
else
    echo -e "${YELLOW}[UYARI]${NC} trufflehog bulunamadı, gizli anahtar taraması atlanıyor."
fi

# Özet Raporu
echo -e "\n${BLUE}Özet Rapor:${NC}"
echo -e "Tüm tarama sonuçları: $REPORT_DIR/"
echo -e "Daha detaylı sonuçlar için her bir rapor dosyasını inceleyebilirsiniz."
echo
echo "Önemli Hatırlatma: Otomatik güvenlik taramaları kapsamlı değildir."
echo "Manuel kod incelemesi ve penetrasyon testleri düzenli olarak yapılmalıdır."
echo
echo -e "${GREEN}Tarama Tamamlandı!${NC}"