from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views


urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        '',
        include('posts.urls')
    ),

    path(
        'api/',
        include('api.urls')
    ),

    path(
        '',
        include('users.urls')
    ),

    path(
        'friends/',
        include('friends.urls')
    ),

    path(
        'notifications/',
        include('notifications.urls')
    ),

    path(
        'messages/',
        include('messaging.urls')
    ),

    path(
        'stories/',
        include('stories.urls')
    ),

    path(
        'groups/',
        include('groups.urls')
    ),

    path(
        'reels/',
        include('reels.urls')
    ),

    path(
        'events/',
        include('events.urls')
    ),

    path(
        'moderation/',
        include('moderation.urls')
    ),

    path(
        'accounts/',
        include('allauth.urls')
    ),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='users/login.html'
        ),
        name='login'
    ),

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset.html',
            email_template_name='users/password_reset_email.html',
            subject_template_name='users/password_reset_subject.txt',
            success_url='/password-reset/done/'
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url='/password-reset-complete/'
        ),
        name='password_reset_confirm'
    ),

    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),
]

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )