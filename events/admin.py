from django.contrib import admin
from .models import Event, EventRSVP

class EventRSVPInline(admin.TabularInline):
    model = EventRSVP
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'start_datetime', 'end_datetime', 'is_online', 'attendee_count')
    list_filter = ('start_datetime', 'is_online', 'creator')
    search_fields = ('title', 'description', 'location', 'creator__username')
    inlines = [EventRSVPInline]

@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'event__title')

