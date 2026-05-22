from django.contrib import admin

from .models import AttendanceRecord, AttendanceSession


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "course_class", "started_at", "ended_at", "status", "created_by")
    list_filter = ("status", "course_class")
    search_fields = ("course_class__class_code", "note")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "student", "status", "method", "confidence", "timestamp")
    list_filter = ("status", "method")
    search_fields = ("student__student_id", "student__full_name", "session__course_class__class_code")
