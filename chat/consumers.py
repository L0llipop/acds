from channels.generic.websocket import AsyncWebsocketConsumer
import json
import datetime
from django.utils import timezone
# import multimodule

class ChatConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.room_name = self.scope['url_route']['kwargs']['room_name']
		self.room_group_name = 'chat_%s' % self.room_name

		# Join room group
		await self.channel_layer.group_add(
			self.room_group_name,
			self.channel_name
		)

		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(
			self.room_group_name,
			self.channel_name
		)

	# Receive message from WebSocket
	async def receive(self, text_data):
		user = str(self.scope["user"])
		# Send message to room group
		if user == 'AnonymousUser':
			message = text_data
			await self.channel_layer.group_send(
				self.room_group_name, 
				{
					'type': 'chat_message',
					'message': f"server: {message}",
				}
			)
		else:
			text_data_json = json.loads(text_data)
			message = text_data_json['message']
			await self.channel_layer.group_send(
				self.room_group_name, 
				{
					'type': 'chat_message',
					'message': f"{user}: {message}",
				}
			)

		# user = str(self.scope["user"])
		# if user == 'AnonymousUser':
		# 	text_data_json = json.loads(text_data)
		# 	message = text_data_json['message']
		# 	await self.channel_layer.group_send(
		# 		self.room_group_name,
		# 		{
		# 			'type': 'chat_message',
		# 			'message': f"free_ip: {message}"
		# 		}
		# 	)

		# else:
		# 	message = text_data
		# 	await self.channel_layer.group_send(
		# 		self.room_group_name,
		# 		{
		# 			'type': 'chat_message',
		# 			'message': f"{user}: {message}"
		# 		}
		# 	)


	# Receive message from room group
	async def chat_message(self, event):
		message = event['message']

		# Send message to WebSocket
		await self.send(text_data=json.dumps({
			'message': f"{message}"
		}))