from django.contrib import admin
from .models import Story


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('author', 'caption', 'created_at', 'expires_at', 'is_active')
    list_filter = ('created_at',)
