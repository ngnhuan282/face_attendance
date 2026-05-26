from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .select_related('student__student_class', 'course_class__course', 'course_class__semester')
        .order_by('-created_at')
    )

    unread_count   = notifications.filter(is_read=False).count()
    danger_count   = notifications.filter(noti_type='absent_danger').count()
    warning_count  = notifications.filter(noti_type='absent_warning').count()

    # Lọc theo loại
    filter_type = request.GET.get('type', '')
    if filter_type in ('absent_warning', 'absent_danger'):
        notifications = notifications.filter(noti_type=filter_type)

    # Lọc chưa đọc
    if request.GET.get('unread') == '1':
        notifications = notifications.filter(is_read=False)

    context = {
        'notifications': notifications,
        'unread_count' : unread_count,
        'danger_count' : danger_count,
        'warning_count': warning_count,
        'filter_type'  : filter_type,
        'active_menu'  : 'notifications',
    }
    return render(request, 'notifications/list.html', context)


@login_required
def mark_read(request, noti_id):
    noti = get_object_or_404(Notification, pk=noti_id)
    noti.is_read = True
    noti.save(update_fields=['is_read'])
    return redirect(request.META.get('HTTP_REFERER', 'notifications:list'))


@login_required
def mark_all_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    return redirect('notifications:list')
