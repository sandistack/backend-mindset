from channels.db import database_sync_to_async
from django.utils import timezone
from apps.core.consumers import BaseConsumer
from .models import Notification
from .serializers import NotificationSerializer


class NotificationConsumer(BaseConsumer):
    """
    WebSocket consumer untuk notifikasi user.
    
    Messages:
    - mark_read: Mark notification as read
    - mark_all_read: Mark all notifications as read
    """
    
    async def on_connect(self):
        self.room_group_name = f'notifications_{self.user.id}'
        
        # Join personal notification room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send unread count
        unread_count = await self.get_unread_count()
        await self.send_message('unread_count', {'count': unread_count})
    
    async def on_disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def handle_mark_read(self, data):
        """Mark notification as read"""
        notification_id = data.get('notification_id')
        await self.mark_as_read(notification_id)
        
        # Send updated unread count
        unread_count = await self.get_unread_count()
        await self.send_message('unread_count', {'count': unread_count})
    
    async def handle_mark_all_read(self, data):
        """Mark all notifications as read"""
        await self.mark_all_as_read()
        await self.send_message('unread_count', {'count': 0})
    
    # Group handlers
    async def new_notification(self, event):
        """Handler untuk notifikasi baru dari sistem lain"""
        await self.send_message('notification', event['notification'])
        
        # Send updated unread count
        unread_count = await self.get_unread_count()
        await self.send_message('unread_count', {'count': unread_count})
    
    # Database operations
    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_as_read(self, notification_id):
        Notification.objects.filter(
            id=notification_id,
            user=self.user
        ).update(is_read=True, read_at=timezone.now())
    
    @database_sync_to_async
    def mark_all_as_read(self):
        Notification.objects.filter(
            user=self.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())


# Helper function untuk mengirim notifikasi dari bagian lain aplikasi
async def send_notification(user_id, notification_type, title, message, data=None):
    """
    Send notification to user via WebSocket.
    
    Usage:
        from apps.notifications.consumers import send_notification
        await send_notification(user.id, 'mention', 'You were mentioned', 'John mentioned you in #general')
    """
    from channels.layers import get_channel_layer
    from .models import Notification
    from channels.db import database_sync_to_async
    
    @database_sync_to_async
    def create_notification():
        return Notification.objects.create(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data or {}
        )
    
    # Save to database
    notification = await create_notification()
    
    # Serialize
    @database_sync_to_async
    def serialize():
        return NotificationSerializer(notification).data
    
    notification_data = await serialize()
    
    # Send via WebSocket
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'notifications_{user_id}',
        {
            'type': 'new_notification',
            'notification': notification_data
        }
    )
