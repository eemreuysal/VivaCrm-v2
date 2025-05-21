"""
WebSocket utilities for sending real-time updates.
"""
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

channel_layer = get_channel_layer()


def send_import_progress(import_job_id: str, data: dict):
    """
    Import işlemi ilerleme güncellemesi gönderir.
    
    Args:
        import_job_id: Import job ID'si
        data: Gönderilecek veri
    """
    room_group_name = f'import_{import_job_id}'
    
    try:
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'import_progress',
                'data': data
            }
        )
    except Exception as e:
        logger.error(f"Error sending import progress: {str(e)}")


def send_import_completed(import_job_id: str, data: dict):
    """
    Import işlemi tamamlandı bildirimi gönderir.
    
    Args:
        import_job_id: Import job ID'si
        data: Sonuç verileri
    """
    room_group_name = f'import_{import_job_id}'
    
    try:
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'import_completed',
                'data': data
            }
        )
    except Exception as e:
        logger.error(f"Error sending import completed: {str(e)}")


def send_import_failed(import_job_id: str, data: dict):
    """
    Import işlemi başarısız bildirimi gönderir.
    
    Args:
        import_job_id: Import job ID'si
        data: Hata verileri
    """
    room_group_name = f'import_{import_job_id}'
    
    try:
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'import_failed',
                'data': data
            }
        )
    except Exception as e:
        logger.error(f"Error sending import failed: {str(e)}")


def send_user_notification(user_id: int, notification: dict):
    """
    Kullanıcıya bildirim gönderir.
    
    Args:
        user_id: Kullanıcı ID'si
        notification: Bildirim verisi
    """
    room_group_name = f'notifications_{user_id}'
    
    try:
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'notification',
                'data': notification
            }
        )
    except Exception as e:
        logger.error(f"Error sending user notification: {str(e)}")