import json
import httpx
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings  # optional if using settings to store key


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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
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
                response.raise_for_status()
                bot_msg = response.json()["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            bot_msg = f"[HTTP Error {e.response.status_code}] {e.response.text}"
        except httpx.RequestError as e:
            bot_msg = f"[Request Error] {str(e)}"
        except Exception as e:
            bot_msg = f"[Unexpected Error] {str(e)}"

        await self.save_bot_message(bot_msg)

        await self.send(text_data=json.dumps({
            "message": bot_msg
        }))
