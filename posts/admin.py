from django.contrib import admin
from .models import Post, Comment, Poll, PollOption, PollVote

class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_excerpt', 'created_at', 'reaction_count_display')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')

    def content_excerpt(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_excerpt.short_description = 'Content'

    def reaction_count_display(self, obj):
        return obj.reaction_count()
    reaction_count_display.short_description = 'Reactions'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'content_excerpt', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username', 'post__content')

    def content_excerpt(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_excerpt.short_description = 'Content'

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'post', 'created_at', 'expires_at')
    inlines = [PollOptionInline]

@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'poll', 'vote_count')

@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'poll', 'option', 'created_at')

