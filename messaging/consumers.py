import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope.get('user')

        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        # Verify user is a participant
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message', '')

        if not message_content.strip():
            return

        message_data = await self.save_message(message_content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
        }))

    @database_sync_to_async
    def check_participant(self):
        from .models import Conversation
        try:
            convo = Conversation.objects.get(id=self.conversation_id)
            return convo.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        from .models import Conversation, Message
        convo = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(
            conversation=convo,
            sender=self.user,
            content=content,
        )
        convo.save()  # update timestamp
        return {
            'id': msg.id,
            'sender': self.user.username,
            'sender_id': self.user.id,
            'content': msg.content,
            'image_url': None,
            'created_at': msg.created_at.strftime('%b %d, %I:%M %p'),
        }
