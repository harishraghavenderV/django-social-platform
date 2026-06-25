from django.urls import path
from . import views, views_2fa, views_analytics

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('settings/notifications/', views.notification_preferences, name='notification_prefs'),
    path('settings/theme/toggle/', views.toggle_theme, name='toggle_theme'),
    path('activity/', views.activity_log_view, name='activity_log'),
    path('analytics/', views_analytics.profile_analytics, name='profile_analytics'),
    path('media-gallery/', views_analytics.media_gallery, name='media_gallery'),
    path('2fa/setup/', views_2fa.setup_2fa, name='setup_2fa'),
    path('2fa/disable/', views_2fa.disable_2fa, name='disable_2fa'),
    path('2fa/verify/', views_2fa.verify_2fa, name='verify_2fa'),
    path('settings/switch-account/<int:user_id>/', views.switch_account, name='switch_account'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
]