from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('unread-count/', views.unread_messages_count, name='unread_messages_count'),
]
