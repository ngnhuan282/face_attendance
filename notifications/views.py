from django.shortcuts import get_object_or_404, redirect, render

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required

from .models import Notification


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def notification_list(request):
    notifications = (
        Notification.objects
        .select_related(
            'student__student_class',
            'course_class__course',
            'course_class__semester',
        )
        .order_by('-created_at')
    )

    total_count   = notifications.count()
    unread_count  = notifications.filter(is_read=False).count()
    danger_count  = notifications.filter(noti_type='absent_danger').count()
    warning_count = notifications.filter(noti_type='absent_warning').count()
    
    # Lọc theo loại
    filter_type = request.GET.get('type', '')
    filter_sem  = request.GET.get('semester', '')
    show_unread = request.GET.get('unread', '')

    if filter_type in ('absent_warning', 'absent_danger'):
        notifications = notifications.filter(noti_type=filter_type)
    if show_unread == '1':
        notifications = notifications.filter(is_read=False)
    if filter_sem:
        notifications = notifications.filter(course_class__semester_id=filter_sem)

    from academics.models import Semester
    semesters = Semester.objects.order_by('-start_date')

    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications/list.html', {
        'page_obj'     : page_obj,
        'total_count'  : total_count,
        'unread_count' : unread_count,
        'danger_count' : danger_count,
        'warning_count': warning_count,
        'filter_type'  : filter_type,
        'filter_sem'   : filter_sem,
        'show_unread'  : show_unread,
        'semesters'    : semesters,
        'active_menu'  : 'notifications',
    })


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def mark_read(request, noti_id):
    noti = get_object_or_404(Notification, pk=noti_id)
    noti.is_read = True
    noti.save(update_fields=['is_read'])
    return redirect(request.META.get('HTTP_REFERER') or 'notifications:list')


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def mark_all_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    return redirect('notifications:list')
