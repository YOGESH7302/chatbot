import json
import httpx
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async



OPENROUTER_API_KEY = "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"


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass
    
    @sync_to_async
    
    def save_user_message(self, message):
        from .models import ChatMessage
        ChatMessage.objects.create(sender="user", message=message)

    @sync_to_async
    def save_bot_message(self, message):
        from .models import ChatMessage
        ChatMessage.objects.create(sender="bot", message=message)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_msg = data.get("message", "")

        
        await self.save_user_message(user_msg)

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistralai/mistral-7b-instruct",
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": user_msg}
                        ]
                    }
                )
                res.raise_for_status()
                bot_msg = res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            bot_msg = f"[Error] {str(e)}"

        
        await self.save_bot_message(bot_msg)

        await self.send(text_data=json.dumps({
            "message": bot_msg
        }))
