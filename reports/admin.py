from django.contrib import admin
from .models import AttendanceReport


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display  = (
        'student', 'course_class',
        'total_sessions', 'present_count', 'absent_count', 'late_count',
        'attendance_rate', 'absent_rate', 'updated_at',
    )
    list_filter   = ('course_class__semester', 'course_class')
    search_fields = ('student__full_name', 'student__student_id', 'course_class__class_code')
    readonly_fields = ('attendance_rate', 'absent_rate', 'updated_at')
