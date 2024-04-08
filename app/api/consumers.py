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
        await self.channel_layer.group_discard(
            "notifications",
            self.channel_name,
        )
        await self.close()

    async def receive(self, text_data):
        print("received: ", text_data)
    
    async def emit_notification(self, event):
        json_data = json.dumps(event)
        await self.send(text_data=json_data)
