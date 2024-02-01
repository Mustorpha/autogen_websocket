from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import openai
import os
import asyncio

from .autogen_chat import AutogenChat

import json

_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']

class AutogenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        session_uuid = self.scope['url_route']['kwargs']['session_uuid']
        # user = self.scope['user']
        # self.conn = ActiveConnection.create(id=session_uuid, user=user, is_active=True)
        response = {
            'type': 'websocket.accept',
            'session_id': str(session_uuid),
            'message': 'Connection made successfully',
            # 'user': user.username,
            'connection_time': str(datetime.now())
        }
        await self.accept()
        await self.send(json.dumps(response))
        self.autogen_chat = AutogenChat(websocket=self)
        asyncio.create_task(self.autogen_chat.start())
    
    async def receive(self, text_data):
        received_data = json.loads(text_data)
        data = received_data["message"]
        if data and data == "END":
            # await self.autogen_chat.client_receive_queue.put("END")
            await self.autogen_chat.client_sent_queue.put("END")
        await self.autogen_chat.client_sent_queue.put(data)
        """
        await self.send(json.dumps({
            'type': 'websocet.send',
            'message': data
        }))
        """

    async def disconnect(self, code):
        disconnection_time = str(datetime.now())
        # self.conn.update(is_active=False, disconnect_at=disconnection_time)
        self.autogen_chat.client_receive_queue.put_nowait("END")
        response = {
            'type': 'websocket.disconnect',
            'message': 'Session was disconnected successfully',
            'disconnection_time': disconnection_time,
            # 'session_durartion': self.conn.connect_at - disconnection_time,
            'status': str(code)
        }
        await self.send(json.dumps(response))
