from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts', views.PostViewSet, basename='post')
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'friend-requests', views.FriendRequestViewSet, basename='friend-request')

urlpatterns = [
    path('', include(router.urls)),
]
