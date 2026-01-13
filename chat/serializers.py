from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatRoom, Message

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender_type', 'sender', 'sender_name', 'message', 'is_read', 'created_at']
        read_only_fields = ['sender', 'sender_name']
    
    def get_sender_name(self, obj):
        if obj.sender:
            full_name = f"{obj.sender.first_name} {obj.sender.last_name}".strip()
            return full_name or obj.sender.username
        return 'Guest'

class ChatRoomSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'user', 'user_name', 'session_id', 'is_active', 
                  'messages', 'unread_count', 'last_message', 'created_at', 'updated_at']
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_staff:
            return obj.messages.filter(is_read=False, sender_type='user').count()
        return obj.messages.filter(is_read=False, sender_type='admin').count()
    
    def get_user_name(self, obj):
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name or obj.user.username
        return f"Guest {obj.session_id[:8] if obj.session_id else 'Unknown'}"
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'message': last_msg.message,
                'sender_type': last_msg.sender_type,
                'created_at': last_msg.created_at
            }
        return None
