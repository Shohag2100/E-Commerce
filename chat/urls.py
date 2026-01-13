from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, AdminChatViewSet

router = DefaultRouter()
router.register('user', ChatViewSet, basename='chat')
router.register('admin', AdminChatViewSet, basename='admin-chat')

urlpatterns = router.urls
