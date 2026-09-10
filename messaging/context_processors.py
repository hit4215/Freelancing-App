def unread_messages_count(request):
    if request.user.is_authenticated:
        try:
            from messaging.models import Message
            count = Message.objects.filter(
                conversation__participants=request.user,
                is_read=False
            ).exclude(sender=request.user).count()
            return {'unread_messages_count': count}
        except Exception:
            return {'unread_messages_count': 0}
    return {'unread_messages_count': 0}
