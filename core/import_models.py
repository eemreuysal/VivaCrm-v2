from django.db import models
import json
import os
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
import uuid
from django.urls import reverse
import hashlib

User = get_user_model()


class ImportHistory(models.Model):
    """Excel import geçmişi modeli"""
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('processing', 'İşleniyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    
    MODULE_CHOICES = [
        ('products', 'Ürünler'),
        ('customers', 'Müşteriler'),
        ('orders', 'Siparişler'),
        ('stock', 'Stok Hareketleri'),
        ('stock_adjustment', 'Stok Düzeltme'),
    ]
    
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file_name = models.CharField(max_length=255, verbose_name="Dosya Adı")
    file_path = models.CharField(max_length=500, verbose_name="Dosya Yolu", blank=True)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name="Modül")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Durum")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Oluşturan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarihi")
    
    # İstatistikler
    success_count = models.IntegerField(default=0, verbose_name="Başarılı")
    error_count = models.IntegerField(default=0, verbose_name="Hatalı")
    processed_count = models.IntegerField(default=0, verbose_name="İşlenen")
    total_count = models.IntegerField(default=0, verbose_name="Toplam")
    
    # Import parametreleri ve detayları
    import_params = models.JSONField(default=dict, blank=True, verbose_name="Import Parametreleri")
    error_details = models.JSONField(default=dict, blank=True, verbose_name="Hata Detayları")
    success_details = models.JSONField(default=dict, blank=True, verbose_name="Başarı Detayları")
    
    # Dosya bilgileri
    file_size = models.BigIntegerField(default=0, verbose_name="Dosya Boyutu (byte)")
    file_hash = models.CharField(max_length=64, blank=True, verbose_name="Dosya Hash")
    
    # Yeniden yükleme için
    can_reload = models.BooleanField(default=True, verbose_name="Yeniden Yüklenebilir")
    parent_import = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='reload_history', verbose_name="Ana Import")
    
    class Meta:
        verbose_name = "Import Geçmişi"
        verbose_name_plural = "Import Geçmişleri"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['module']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.get_module_display()} - {self.file_name} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        return reverse('core:import-detail', kwargs={'uid': self.uid})
    
    def get_progress_percentage(self):
        """İlerleme yüzdesini hesapla"""
        if self.total_count == 0:
            return 0
        return round((self.processed_count / self.total_count) * 100, 1)
    
    def get_file_size_display(self):
        """Dosya boyutunu okunabilir formatta göster"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_duration(self):
        """İşlem süresini hesapla"""
        if not self.completed_at:
            return None
        duration = self.completed_at - self.created_at
        return duration.total_seconds()
    
    def get_duration_display(self):
        """İşlem süresini okunabilir formatta göster"""
        duration = self.get_duration()
        if not duration:
            return "-"
        
        if duration < 60:
            return f"{int(duration)} saniye"
        elif duration < 3600:
            return f"{int(duration/60)} dakika"
        else:
            hours = int(duration/3600)
            minutes = int((duration % 3600) / 60)
            return f"{hours} saat {minutes} dakika"
    
    def mark_completed(self):
        """İmport işlemini tamamlandı olarak işaretle"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message=None):
        """İmport işlemini başarısız olarak işaretle"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        if error_message:
            self.error_details['general_error'] = error_message
        self.save()
    
    def add_error(self, row_number, error_message, row_data=None):
        """Belirli bir satır için hata ekle"""
        if 'rows' not in self.error_details:
            self.error_details['rows'] = {}
        
        error_info = {
            'message': error_message,
            'timestamp': timezone.now().isoformat()
        }
        
        if row_data:
            error_info['data'] = row_data
            
        self.error_details['rows'][str(row_number)] = error_info
        self.error_count += 1
        self.save()
    
    def add_success(self, row_number, created_id=None, updated_id=None, details=None):
        """Başarılı işlem ekle"""
        if 'rows' not in self.success_details:
            self.success_details['rows'] = {}
        
        success_info = {
            'timestamp': timezone.now().isoformat()
        }
        
        if created_id:
            success_info['created_id'] = created_id
        if updated_id:
            success_info['updated_id'] = updated_id
        if details:
            success_info['details'] = details
            
        self.success_details['rows'][str(row_number)] = success_info
        self.success_count += 1
        self.save()
    
    def update_progress(self, processed=0, success=0, error=0):
        """İlerleme istatistiklerini güncelle"""
        self.processed_count += processed
        self.success_count += success
        self.error_count += error
        self.save()
    
    def store_file(self, file):
        """Dosyayı sakla ve bilgileri kaydet"""
        # Dosya yolu oluştur
        file_path = f"imports/{self.module}/{timezone.now().strftime('%Y/%m')}/{self.uid}_{file.name}"
        
        # Dosyayı kaydet
        saved_path = default_storage.save(file_path, file)
        self.file_path = saved_path
        self.file_size = file.size
        
        # Hash hesapla
        file.seek(0)
        self.file_hash = hashlib.sha256(file.read()).hexdigest()
        file.seek(0)
        
        self.save()
        return saved_path
    
    def get_stored_file(self):
        """Saklanan dosyayı getir"""
        if self.file_path and default_storage.exists(self.file_path):
            return default_storage.open(self.file_path)
        return None
    
    def can_reload_import(self):
        """Import'un yeniden yüklenip yüklenemeyeceğini kontrol et"""
        return self.can_reload and self.file_path and default_storage.exists(self.file_path)
    
    def create_reload(self, user):
        """Bu import'un yeniden yüklemesini oluştur"""
        reload_import = ImportHistory.objects.create(
            file_name=self.file_name,
            file_path=self.file_path,
            module=self.module,
            created_by=user,
            import_params=self.import_params,
            file_size=self.file_size,
            file_hash=self.file_hash,
            parent_import=self,
            total_count=self.total_count
        )
        return reload_import