from .models import Notification


def unread_notifications_count(request):  
    if not request.user.is_authenticated:
        return {'unread_noti_count': 0}

    notifications = Notification.objects.filter(is_read=False)
    if (
        getattr(request, 'is_teacher_group', False)
        and not getattr(request, 'is_admin_group', False)
    ):
        teacher = getattr(request.user, 'teacher', None)
        if teacher is None:
            return {'unread_noti_count': 0}
        notifications = notifications.filter(course_class__teacher=teacher)

    count = notifications.count()
    return {'unread_noti_count': count}
