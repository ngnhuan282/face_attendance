from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Case, Exists, OuterRef, Value, When
from django.shortcuts import get_object_or_404, redirect, render

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required

from .models import Notification, NotificationRead


def _teacher_scope(request):
    if request.is_teacher_group and not request.is_admin_group:
        teacher = getattr(request.user, 'teacher', None)
        if teacher is None:
            raise PermissionDenied
        return teacher
    return None


def _notification_queryset(request):
    read_receipts = NotificationRead.objects.filter(
        notification=OuterRef('pk'),
        user=request.user,
    )
    notifications = (
        Notification.objects
        .select_related(
            'student__student_class',
            'course_class__course',
            'course_class__semester',
        )
        .annotate(has_read_receipt=Exists(read_receipts))
        .annotate(
            is_read_for_user=Case(
                When(is_read=True, then=Value(True)),
                When(has_read_receipt=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .order_by('is_read_for_user', '-created_at')
    )

    teacher = _teacher_scope(request)
    if teacher:
        notifications = notifications.filter(course_class__teacher=teacher)

    return notifications, teacher


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def notification_list(request):
    notifications, teacher = _notification_queryset(request)

    total_count   = notifications.count()
    unread_count  = notifications.filter(is_read_for_user=False).count()
    danger_count  = notifications.filter(noti_type='absent_danger').count()
    warning_count = notifications.filter(noti_type='absent_warning').count()
    
    # Lọc theo loại
    filter_type = request.GET.get('type', '')
    filter_sem  = request.GET.get('semester', '')
    show_unread = request.GET.get('unread', '')

    if filter_type in ('absent_warning', 'absent_danger'):
        notifications = notifications.filter(noti_type=filter_type)
    if show_unread == '1':
        notifications = notifications.filter(is_read_for_user=False)
    if filter_sem:
        notifications = notifications.filter(course_class__semester_id=filter_sem)

    from academics.models import Semester
    semesters = Semester.objects.order_by('-start_date')
    if teacher:
        semesters = semesters.filter(course_classes__teacher=teacher).distinct()

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
    notifications, _ = _notification_queryset(request)
    noti = get_object_or_404(notifications, pk=noti_id)
    NotificationRead.objects.get_or_create(
        notification=noti,
        user=request.user,
    )
    return redirect(request.META.get('HTTP_REFERER') or 'notifications:list')


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def mark_all_read(request):
    notifications, _ = _notification_queryset(request)
    unread_ids = notifications.filter(is_read_for_user=False).values_list('pk', flat=True)
    NotificationRead.objects.bulk_create(
        [
            NotificationRead(notification_id=noti_id, user=request.user)
            for noti_id in unread_ids
        ],
        ignore_conflicts=True,
    )
    return redirect('notifications:list')
