from django.contrib import admin
from .models import ChatRoom, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender_type', 'sender', 'message', 'is_read', 'created_at']
    can_delete = False
    ordering = ['created_at']

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'session_id']
    inlines = [MessageInline]
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'sender_type', 'sender', 'message', 'is_read', 'created_at']
    list_filter = ['sender_type', 'is_read', 'created_at']
    search_fields = ['message', 'sender__username']
    readonly_fields = ['created_at']