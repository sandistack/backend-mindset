from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class BaseConsumer(AsyncJsonWebsocketConsumer):
    """Base consumer with common functionality"""
    
    async def connect(self):
        # Check authentication
        if self.scope['user'].is_anonymous:
            await self.close(code=4001)
            return
        
        self.user = self.scope['user']
        await self.on_connect()
    
    async def on_connect(self):
        """Override in subclass"""
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.on_disconnect(close_code)
    
    async def on_disconnect(self, close_code):
        """Override in subclass"""
        pass
    
    async def receive_json(self, content):
        """Route message to handler based on type"""
        message_type = content.get('type', '')
        handler = getattr(self, f'handle_{message_type}', None)
        
        if handler:
            await handler(content.get('data', {}))
        else:
            await self.send_error(f'Unknown message type: {message_type}')
    
    async def send_message(self, message_type, data):
        await self.send_json({
            'type': message_type,
            'data': data
        })
    
    async def send_error(self, message):
        await self.send_json({
            'type': 'error',
            'message': message
        })
