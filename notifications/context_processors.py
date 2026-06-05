from .models import Notification


def unread_notifications_count(request):  
    if not request.user.is_authenticated:
        return {'unread_noti_count': 0}

    count = Notification.objects.filter(is_read=False).count()
    return {'unread_noti_count': count}
