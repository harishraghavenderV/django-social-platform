from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('post/create/', views.post_create, name='post_create'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:pk>/react/', views.post_react, name='post_react'),
    path('post/create-poll/', views.create_poll, name='create_poll'),
    path('poll/<int:pk>/vote/', views.vote_poll, name='vote_poll'),
    path('post/<int:pk>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:pk>/share/', views.post_share, name='post_share'),
    path('bookmarks/', views.bookmarks_list, name='bookmarks_list'),
    path('search/', views.search, name='search'),
    path('explore/', views.explore, name='explore'),
    path('hashtag/<str:tag>/', views.hashtag_feed, name='hashtag_feed'),
    path('api/feed/', views.home_feed_api, name='home_feed_api'),
]