from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_story, name='create_story'),
    path('view/<int:user_id>/', views.view_stories, name='view_stories'),
    path('data/', views.story_data, name='story_data'),
]
