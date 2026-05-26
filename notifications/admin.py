from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = (
        'student', 'course_class', 'noti_type',
        'absent_count', 'total_sessions', 'absent_percent',
        'is_read', 'created_at',
    )
    list_filter   = ('noti_type', 'is_read', 'course_class__semester')
    search_fields = ('student__full_name', 'student__student_id', 'course_class__class_code')
    actions       = ['mark_as_read']

    @admin.action(description='Đánh dấu đã đọc')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
