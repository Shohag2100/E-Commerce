from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer

class ChatViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    def get_or_create_room(self, request):
        if request.user.is_authenticated:
            room, created = ChatRoom.objects.get_or_create(user=request.user)
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            room, created = ChatRoom.objects.get_or_create(session_id=session_id)
        return room
    
    def list(self, request):
        """Get user's chat room"""
        room = self.get_or_create_room(request)
        serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send a message in user's chat room"""
        room = self.get_or_create_room(request)
        message_text = request.data.get('message', '').strip()
        
        if not message_text:
            return Response(
                {'error': 'Message cannot be empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = Message.objects.create(
            room=room,
            sender_type='user',
            sender=request.user if request.user.is_authenticated else None,
            message=message_text
        )
        
        # Update room's updated_at
        room.save()
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Mark admin messages as read"""
        room = self.get_or_create_room(request)
        updated = room.messages.filter(sender_type='admin', is_read=False).update(is_read=True)
        return Response({'status': 'success', 'marked_read': updated})

class AdminChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        """List all chat rooms for admin"""
        rooms = ChatRoom.objects.filter(is_active=True)
        serializer = ChatRoomSerializer(rooms, many=True, context={'request': request})
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get specific chat room"""
        try:
            room = ChatRoom.objects.get(pk=pk)
            # Mark user messages as read when admin opens the chat
            room.messages.filter(sender_type='user', is_read=False).update(is_read=True)
            serializer = ChatRoomSerializer(room, context={'request': request})
            return Response(serializer.data)
        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Chat room not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send message as admin"""
        try:
            room = ChatRoom.objects.get(pk=pk)
            message_text = request.data.get('message', '').strip()
            
            if not message_text:
                return Response(
                    {'error': 'Message cannot be empty'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            message = Message.objects.create(
                room=room,
                sender_type='admin',
                sender=request.user,
                message=message_text
            )
            
            # Update room's updated_at
            room.save()
            
            serializer = MessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Chat room not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def close_chat(self, request, pk=None):
        """Close/archive a chat room"""
        try:
            room = ChatRoom.objects.get(pk=pk)
            room.is_active = False
            room.save()
            return Response({'status': 'Chat room closed'})
        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Chat room not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )