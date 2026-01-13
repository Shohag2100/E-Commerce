from django.db import models
from django.contrib.auth.models import User

class ChatRoom(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms', null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.user:
            return f"Chat Room - {self.user.username}"
        return f"Chat Room - Guest {self.session_id[:8]}"

class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender_type}: {self.message[:30]}"