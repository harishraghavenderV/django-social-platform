import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PostConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = 'posts_feed'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def new_post(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_post',
            'post_html': event['post_html'],
            'author_username': event['author_username'],
        }))

    async def post_like_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'post_like_update',
            'post_id': event['post_id'],
            'like_count': event['like_count'],
        }))

    async def post_comment_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'post_comment_update',
            'post_id': event['post_id'],
            'comment_count': event['comment_count'],
            'comment_html': event.get('comment_html'),
        }))
