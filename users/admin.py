from django.contrib import admin
from .models import UserProfile
from .models_badges import Badge, UserBadge
from .models_activity import ActivityLog


admin.site.register(UserProfile)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'criteria', 'icon', 'color')
    search_fields = ('name', 'criteria')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('badge',)
    search_fields = ('user__username',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'description', 'created_at')
    list_filter = ('action_type',)
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at',)