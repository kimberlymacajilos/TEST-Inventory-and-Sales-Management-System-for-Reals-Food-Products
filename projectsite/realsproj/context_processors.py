from .models import Notifications

def notifications_context(request):
    notifications = Notifications.objects.filter(is_read=False).order_by('-created_at')[:5]
    unread_count = Notifications.objects.filter(is_read=False).count()

    return {
        "notifications": notifications,
        "unread_count": unread_count,
    }
