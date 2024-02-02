from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        await self.channel_layer.group_add(
            "notifications",
            self.channel_name,
        )

    async def disconnect(self, close_code):
        await self.close()
        
        await self.channel_layer.group_discard(
            "notifications",
            self.channel_name,
        )

    async def receive(self, text_data):
        #Do something on receive
        pass
    
    async def send(self):
        #Do something on send
        pass
