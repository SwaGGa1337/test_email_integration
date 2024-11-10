import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import EmailAccount
from .email_handlers import EmailHandler

class EmailSyncConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        account_id = data.get('account_id')
        
        try:
            account = await database_sync_to_async(
                EmailAccount.objects.get
            )(id=account_id)
            
            handler = EmailHandler(account)
            
            await self.send(json.dumps({
                'type': 'sync_status',
                'status': 'starting',
                'message': 'Начало синхронизации...'
            }))

            async for progress_data in handler.process_messages():
                await self.send(json.dumps({
                    'type': 'sync_status',
                    'status': 'processing',
                    **progress_data
                }))

            await self.send(json.dumps({
                'type': 'sync_status',
                'status': 'completed',
                'message': 'Синхронизация завершена'
            }))

        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            })) 