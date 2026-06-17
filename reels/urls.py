from django.urls import path
from . import views

app_name = 'reels'

urlpatterns = [
    path('', views.reels_feed, name='feed'),
    path('create/', views.create_reel, name='create'),
    path('<int:pk>/', views.reel_detail, name='detail'),
    path('<int:pk>/like/', views.reel_like, name='like'),
    path('<int:pk>/comment/', views.reel_comment, name='comment'),
]
