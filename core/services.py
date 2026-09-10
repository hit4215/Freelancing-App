from .models import Notification

def send_notification(recipient, title, message, link='', notification_type='SYSTEM', actor=None):
    """
    Utility helper to create in-app notifications for users.
    """
    if not recipient:
        return None
    # Don't notify oneself if actor is recipient
    if actor and actor == recipient:
        return None
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
