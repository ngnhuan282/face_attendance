from django.contrib import admin
from .models import Notification, NotificationRead


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = (
        'student', 'course_class', 'noti_type',
        'absent_count', 'total_sessions', 'absent_percent',
        'created_at',
    )
    list_filter   = ('noti_type', 'course_class__semester')
    search_fields = ('student__full_name', 'student__student_id', 'course_class__class_code')


@admin.register(NotificationRead)
class NotificationReadAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'read_at')
    list_filter = ('read_at',)
    search_fields = (
        'notification__student__full_name',
        'notification__student__student_id',
        'notification__course_class__class_code',
        'user__username',
    )
