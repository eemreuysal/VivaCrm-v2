# core/models_import.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class DetailedImportResult(models.Model):
    """Detaylı içe aktarma sonuçlarını takip eden model"""
    
    # İlişkili içe aktarma kayıtları
    import_task = models.ForeignKey(
        'ImportTask', 
        on_delete=models.CASCADE, 
        related_name='detailed_results',
        verbose_name='İçe Aktarma Görevi'
    )
    
    # Satır bilgileri
    row_number = models.IntegerField(verbose_name='Satır Numarası')
    data = models.JSONField(verbose_name='Veri')
    
    # İşlem durumu
    STATUS_CHOICES = [
        ('created', 'Oluşturuldu'),
        ('updated', 'Güncellendi'),
        ('skipped', 'Atlandı'),
        ('failed', 'Başarısız'),
        ('partial', 'Kısmi Başarılı'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        verbose_name='Durum'
    )
    
    # Detaylı sonuç bilgileri
    fields_updated = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Güncellenen Alanlar'
    )
    fields_failed = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Başarısız Alanlar'
    )
    
    # Hata bilgileri
    error_message = models.TextField(
        null=True, 
        blank=True,
        verbose_name='Hata Mesajı'
    )
    error_details = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Hata Detayları'
    )
    
    # Bağımlı işlemler
    dependent_operations = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='Bağımlı İşlemler'
    )
    
    # Zaman damgaları
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi'
    )
    
    class Meta:
        verbose_name = 'Detaylı İçe Aktarma Sonucu'
        verbose_name_plural = 'Detaylı İçe Aktarma Sonuçları'
        ordering = ['import_task', 'row_number']
        
    def __str__(self):
        return f"{self.import_task} - Satır {self.row_number}: {self.get_status_display()}"


class ImportSummary(models.Model):
    """İçe aktarma özeti modeli"""
    
    import_task = models.OneToOneField(
        'ImportTask',
        on_delete=models.CASCADE,
        related_name='summary',
        verbose_name='İçe Aktarma Görevi'
    )
    
    # Sayaçlar
    total_rows = models.IntegerField(
        default=0,
        verbose_name='Toplam Satır'
    )
    successful_rows = models.IntegerField(
        default=0,
        verbose_name='Başarılı Satır'
    )
    failed_rows = models.IntegerField(
        default=0,
        verbose_name='Başarısız Satır'
    )
    skipped_rows = models.IntegerField(
        default=0,
        verbose_name='Atlanan Satır'
    )
    partial_rows = models.IntegerField(
        default=0,
        verbose_name='Kısmi Başarılı Satır'
    )
    
    # İşlem sayaçları
    created_count = models.IntegerField(
        default=0,
        verbose_name='Oluşturulan Kayıt'
    )
    updated_count = models.IntegerField(
        default=0,
        verbose_name='Güncellenen Kayıt'
    )
    
    # Alan başına başarı oranları
    field_success_rates = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Alan Başarı Oranları'
    )
    
    # Genel bilgiler
    error_summary = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Hata Özeti'
    )
    
    # Zaman bilgileri
    processing_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name='İşlem Süresi'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Güncellenme Tarihi'
    )
    
    class Meta:
        verbose_name = 'İçe Aktarma Özeti'
        verbose_name_plural = 'İçe Aktarma Özetleri'
        
    def __str__(self):
        success_rate = (self.successful_rows / self.total_rows * 100) if self.total_rows > 0 else 0
        return f"{self.import_task} - %{success_rate:.1f} Başarılı"
    
    @property
    def success_rate(self):
        """Başarı oranını hesapla"""
        if self.total_rows == 0:
            return 0
        return (self.successful_rows / self.total_rows) * 100
    
    @property
    def partial_success_rate(self):
        """Kısmi başarı oranını hesapla"""
        if self.total_rows == 0:
            return 0
        return ((self.successful_rows + self.partial_rows) / self.total_rows) * 100


class ImportTask(models.Model):
    """İçe aktarma görevi ana modeli"""
    
    TYPE_CHOICES = [
        ('product', 'Ürün'),
        ('customer', 'Müşteri'),
        ('order', 'Sipariş'),
        ('stock', 'Stok'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('processing', 'İşleniyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
        ('partial', 'Kısmi Başarılı'),
    ]
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Tür'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Durum'
    )
    
    file_name = models.CharField(
        max_length=255,
        verbose_name='Dosya Adı'
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='Dosya Yolu'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Oluşturan'
    )
    
    # İlerleme takibi
    progress = models.IntegerField(
        default=0,
        verbose_name='İlerleme (%)'
    )
    current_row = models.IntegerField(
        default=0,
        verbose_name='İşlenen Satır'
    )
    
    # Zaman damgaları
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Başlangıç Zamanı'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bitiş Zamanı'
    )
    
    class Meta:
        verbose_name = 'İçe Aktarma Görevi'
        verbose_name_plural = 'İçe Aktarma Görevleri'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_type_display()} İçe Aktarma - {self.file_name}"
    
    @property
    def duration(self):
        """İşlem süresini hesapla"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def update_status(self):
        """Durumu detaylı sonuçlara göre güncelle"""
        if hasattr(self, 'summary'):
            summary = self.summary
            if summary.failed_rows > 0 and summary.successful_rows == 0:
                self.status = 'failed'
            elif summary.failed_rows > 0 or summary.partial_rows > 0:
                self.status = 'partial'
            elif summary.successful_rows == summary.total_rows:
                self.status = 'completed'
            else:
                self.status = 'processing'
            self.save()