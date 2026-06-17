from django.urls import path
from . import views

urlpatterns = [
    path('', views.friends_list, name='friends_list'),
    path('request/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('request/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('request/decline/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('request/cancel/<int:request_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
]
