"""
WebSocket consumers for real-time updates in VivaCRM v2.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from core.models_import import ImportJob

logger = logging.getLogger(__name__)


class ImportProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time import progress updates.
    """
    
    async def connect(self):
        """
        WebSocket bağlantısı kurulduğunda çalışır.
        """
        self.import_job_id = self.scope['url_route']['kwargs']['import_job_id']
        self.room_group_name = f'import_{self.import_job_id}'
        
        # Kullanıcı kimlik doğrulamasını kontrol et
        user = self.scope["user"]
        if isinstance(user, AnonymousUser):
            # Anonim kullanıcıları reddet
            await self.close()
            return
        
        # Room grubuna katıl
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # İlk durum güncellemesini gönder
        await self.send_initial_status()
    
    async def disconnect(self, close_code):
        """
        WebSocket bağlantısı kapatıldığında çalışır.
        """
        # Room grubundan ayrıl
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        İstemciden mesaj alındığında çalışır.
        """
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'get_status':
                await self.send_current_status()
            elif command == 'cancel':
                await self.cancel_import()
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Geçersiz JSON formatı'
            }))
    
    async def send_initial_status(self):
        """
        Bağlantı kurulduğunda ilk durum bilgisini gönderir.
        """
        import_job = await self.get_import_job()
        if import_job:
            await self.send(text_data=json.dumps({
                'type': 'initial_status',
                'data': await self.serialize_import_job(import_job)
            }))
    
    async def send_current_status(self):
        """
        Mevcut durum bilgisini gönderir.
        """
        import_job = await self.get_import_job()
        if import_job:
            await self.send(text_data=json.dumps({
                'type': 'status_update',
                'data': await self.serialize_import_job(import_job)
            }))
    
    async def cancel_import(self):
        """
        Import işlemini iptal eder.
        """
        import_job = await self.get_import_job()
        if import_job and import_job.status in ['pending', 'processing']:
            await self.update_import_status('cancelled')
            await self.send(text_data=json.dumps({
                'type': 'cancelled',
                'message': 'İmport işlemi iptal edildi'
            }))
    
    # Broadcast messages from channel layer
    
    async def import_progress(self, event):
        """
        İlerleme güncellemelerini broadcast eder.
        """
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'data': event['data']
        }))
    
    async def import_completed(self, event):
        """
        Tamamlama bildirimini broadcast eder.
        """
        await self.send(text_data=json.dumps({
            'type': 'completed',
            'data': event['data']
        }))
    
    async def import_failed(self, event):
        """
        Hata bildirimini broadcast eder.
        """
        await self.send(text_data=json.dumps({
            'type': 'failed',
            'data': event['data']
        }))
    
    # Database operations
    
    @database_sync_to_async
    def get_import_job(self):
        """
        Import job'ı veritabanından alır.
        """
        try:
            return ImportJob.objects.get(id=self.import_job_id)
        except ImportJob.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_import_status(self, status):
        """
        Import job durumunu günceller.
        """
        try:
            import_job = ImportJob.objects.get(id=self.import_job_id)
            import_job.status = status
            import_job.save()
            return True
        except ImportJob.DoesNotExist:
            return False
    
    @database_sync_to_async
    def serialize_import_job(self, import_job):
        """
        Import job'ı JSON-serializable formata dönüştürür.
        """
        return {
            'id': str(import_job.id),
            'status': import_job.status,
            'progress': float(import_job.progress),
            'total_rows': import_job.total_rows,
            'processed_rows': import_job.processed_rows,
            'success_count': import_job.success_count,
            'error_count': import_job.error_count,
            'current_chunk': import_job.current_chunk,
            'total_chunks': import_job.total_chunks,
            'import_type': import_job.import_type,
            'file_name': import_job.file_name,
            'created_at': import_job.created_at.isoformat() if import_job.created_at else None,
            'started_at': import_job.started_at.isoformat() if import_job.started_at else None,
            'completed_at': import_job.completed_at.isoformat() if import_job.completed_at else None,
            'error_message': import_job.error_message,
            'result_summary': import_job.result_summary,
        }


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Genel bildirimler için WebSocket consumer.
    """
    
    async def connect(self):
        """
        WebSocket bağlantısı kurulduğunda çalışır.
        """
        user = self.scope["user"]
        if isinstance(user, AnonymousUser):
            await self.close()
            return
        
        self.user_id = user.id
        self.room_group_name = f'notifications_{self.user_id}'
        
        # Room grubuna katıl
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        WebSocket bağlantısı kapatıldığında çalışır.
        """
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def notification(self, event):
        """
        Bildirimleri broadcast eder.
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))