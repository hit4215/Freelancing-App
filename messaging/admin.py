from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'body', 'is_read', 'created_at')
    readonly_fields = ('sender', 'body', 'created_at')
    can_delete = True

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'job', 'message_count', 'updated_at', 'created_at')
    filter_horizontal = ('participants',)
    search_fields = ('subject', 'participants__username')
    list_filter = ('updated_at',)
    inlines = [MessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'short_body', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('body', 'sender__username')

    def short_body(self, obj):
        return obj.body[:60]
    short_body.short_description = "Message Preview"
