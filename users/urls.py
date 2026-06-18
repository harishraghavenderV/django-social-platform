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
    # Instagram Graph API OAuth
    path('instagram/connect/', views.instagram_connect, name='instagram_connect'),
    path('instagram/callback/', views.instagram_callback, name='instagram_callback'),
    path('instagram/disconnect/', views.instagram_disconnect, name='instagram_disconnect'),
    path('instagram/sync/', views.instagram_sync_now, name='instagram_sync'),
    path('instagram/toggle-autosync/', views.instagram_toggle_autosync, name='instagram_toggle_autosync'),
]