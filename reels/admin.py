from django.contrib import admin
from .models import Reel, ReelComment

@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = ('author', 'caption', 'created_at', 'view_count', 'like_count', 'comment_count')
    list_filter = ('created_at', 'author')
    search_fields = ('caption', 'author__username')
    readonly_fields = ('created_at', 'view_count')

@admin.register(ReelComment)
class ReelCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'reel', 'content', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username')

