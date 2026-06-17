from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('block/<str:username>/', views.toggle_block_user, name='toggle_block'),
    path('blocked/', views.blocked_list, name='blocked_list'),
    path('report/', views.report_content, name='report_content'),
]
