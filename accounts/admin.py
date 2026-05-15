from django.contrib import admin

from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
	list_display = ('teacher_id', 'user', 'department', 'phone')
	list_filter = ('department',)
	search_fields = ('teacher_id', 'user__username', 'user__first_name', 'user__last_name')
