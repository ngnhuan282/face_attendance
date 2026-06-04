from django.contrib import admin
from .models import Student, StudentClass


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ['class_code', 'class_name', 'department', 'intake_year']
    search_fields = ['class_code', 'class_name']
    list_filter = ['department', 'intake_year']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'student_class', 'email', 'is_active', 'has_photo']
    search_fields = ['student_id', 'full_name', 'email']
    list_filter = ['student_class', 'is_active']
    readonly_fields = ['created_at']

    @admin.display(boolean=True, description='Có ảnh')
    def has_photo(self, obj):
        return bool(obj.photo)
