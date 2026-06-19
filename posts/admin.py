from django.contrib import admin
from .models import Post, Comment, Poll, PollOption, PollVote, Reaction, CommentReaction, Share, HashTag, PostMedia

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

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'post__content')

@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'comment__content')

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'original_post__content')

@admin.register(HashTag)
class HashTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ('post', 'media_type', 'order', 'created_at')
    list_filter = ('media_type', 'created_at')
    search_fields = ('post__content', 'post__author__username')



