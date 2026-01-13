import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat'
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message', '').strip()
            sender_type = data.get('sender_type', 'user')
            
            if not message:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Message cannot be empty'
                }))
                return
            
            # Save message to database
            saved_message = await self.save_message(message, sender_type)
            
            if saved_message:
                # Broadcast message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': saved_message['message'],
                        'sender_type': saved_message['sender_type'],
                        'sender_name': saved_message['sender_name'],
                        'created_at': saved_message['created_at'],
                        'id': saved_message['id']
                    }
                )
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['id'],
            'message': event['message'],
            'sender_type': event['sender_type'],
            'sender_name': event['sender_name'],
            'created_at': event['created_at']
        }))
    
    @database_sync_to_async
    def save_message(self, message, sender_type):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            user = self.scope.get('user')
            
            msg = Message.objects.create(
                room=room,
                sender_type=sender_type,
                sender=user if user.is_authenticated else None,
                message=message
            )
            
            # Update room timestamp
            room.save()
            
            sender_name = 'Guest'
            if msg.sender:
                full_name = f"{msg.sender.first_name} {msg.sender.last_name}".strip()
                sender_name = full_name or msg.sender.username
            
            return {
                'id': msg.id,
                'message': msg.message,
                'sender_type': msg.sender_type,
                'sender_name': sender_name,
                'created_at': msg.created_at.isoformat()
            }
        except ChatRoom.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error saving message: {e}")
            return None