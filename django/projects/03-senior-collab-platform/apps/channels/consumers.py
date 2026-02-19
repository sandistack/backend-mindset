from channels.db import database_sync_to_async
from apps.core.consumers import BaseConsumer
from .models import Channel, Message
from .serializers import MessageSerializer

class ChatConsumer(BaseConsumer):
    """
    WebSocket consumer untuk chat channel.
    
    Messages:
    - message: Send new message
    - typing: Typing indicator
    - read: Mark messages as read
    """
    
    async def on_connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group_name = f'chat_{self.channel_id}'
        
        # Verify access
        has_access = await self.check_access()
        if not has_access:
            await self.close(code=4003)
            return
        
        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update online status
        await self.set_online(True)
        await self.broadcast_presence()
    
    async def on_disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.set_online(False)
        await self.broadcast_presence()
    
    async def handle_message(self, data):
        """Handle new message"""
        content = data.get('content')
        attachments = data.get('attachments', [])
        
        # Save message
        message = await self.save_message(content, attachments)
        message_data = await self.serialize_message(message)
        
        # Broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'new_message',
                'message': message_data
            }
        )
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user_id': str(self.user.id),
                'user_name': self.user.get_full_name(),
                'is_typing': data.get('is_typing', False)
            }
        )
    
    # Group handlers
    async def new_message(self, event):
        await self.send_message('message', event['message'])
    
    async def user_typing(self, event):
        if event['user_id'] != str(self.user.id):
            await self.send_message('typing', {
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            })
    
    # Database operations
    @database_sync_to_async
    def check_access(self):
        try:
            channel = Channel.objects.get(id=self.channel_id)
            if channel.type == 'public':
                return channel.workspace.members.filter(user=self.user).exists()
            return channel.members.filter(id=self.user.id).exists()
        except Channel.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, attachments):
        channel = Channel.objects.get(id=self.channel_id)
        return Message.objects.create(
            channel=channel,
            user=self.user,
            content=content,
            attachments=attachments
        )
    
    @database_sync_to_async
    def serialize_message(self, message):
        return MessageSerializer(message).data
    
    @database_sync_to_async
    def set_online(self, is_online):
        from django.core.cache import cache
        cache_key = f'user_online_{self.user.id}'
        if is_online:
            cache.set(cache_key, True, 300)  # 5 minutes
        else:
            cache.delete(cache_key)
    
    async def broadcast_presence(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': str(self.user.id)
            }
        )
    
    async def presence_update(self, event):
        online_users = await self.get_online_users()
        await self.send_message('presence', {'online_users': online_users})
    
    @database_sync_to_async
    def get_online_users(self):
        from django.core.cache import cache
        channel = Channel.objects.get(id=self.channel_id)
        members = channel.workspace.members.values_list('user_id', flat=True)
        
        online = []
        for user_id in members:
            if cache.get(f'user_online_{user_id}'):
                online.append(str(user_id))
        return online
