from channels.db import database_sync_to_async
from apps.core.consumers import BaseConsumer
from .models import Document
from .services import DocumentService

class DocumentConsumer(BaseConsumer):
    """
    WebSocket consumer untuk collaborative document editing.
    
    Messages:
    - join: Join document session
    - leave: Leave document session
    - update: Send document update
    - cursor: Send cursor position
    """
    
    async def on_connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'
        
        # Verify access
        has_access = await self.check_access()
        if not has_access:
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current document state
        document = await self.get_document()
        await self.send_message('document_state', {
            'content': document.content,
            'version': document.version
        })
        
        # Notify others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': str(self.user.id),
                'user_name': self.user.get_full_name()
            }
        )
    
    async def on_disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': str(self.user.id)
            }
        )
    
    # Message handlers
    async def handle_update(self, data):
        """Handle document update"""
        content = data.get('content')
        version = data.get('version')
        
        # Save to database
        new_version = await self.save_document(content, version)
        
        # Broadcast to all clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'document_updated',
                'content': content,
                'version': new_version,
                'user_id': str(self.user.id)
            }
        )
    
    async def handle_cursor(self, data):
        """Handle cursor position update"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_moved',
                'user_id': str(self.user.id),
                'user_name': self.user.get_full_name(),
                'position': data.get('position')
            }
        )
    
    # Group message handlers (from channel_layer.group_send)
    async def user_joined(self, event):
        await self.send_message('user_joined', {
            'user_id': event['user_id'],
            'user_name': event['user_name']
        })
    
    async def user_left(self, event):
        await self.send_message('user_left', {
            'user_id': event['user_id']
        })
    
    async def document_updated(self, event):
        # Don't send to the user who made the change
        if event['user_id'] != str(self.user.id):
            await self.send_message('document_updated', {
                'content': event['content'],
                'version': event['version'],
                'user_id': event['user_id']
            })
    
    async def cursor_moved(self, event):
        if event['user_id'] != str(self.user.id):
            await self.send_message('cursor_moved', {
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'position': event['position']
            })
    
    # Database operations
    @database_sync_to_async
    def check_access(self):
        try:
            document = Document.objects.get(id=self.document_id)
            return document.workspace.members.filter(user=self.user).exists()
        except Document.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_document(self):
        return Document.objects.get(id=self.document_id)
    
    @database_sync_to_async
    def save_document(self, content, version):
        document = Document.objects.get(id=self.document_id)
        document.content = content
        document.version += 1
        document.save()
        
        # Create version history
        DocumentService.create_version(document, self.user)
        
        return document.version
