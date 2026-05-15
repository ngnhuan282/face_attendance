from django.contrib import admin

from .models import Faculty, Department, AcademicYear, Semester

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
	list_display = ('code', 'name')
	search_fields = ('code', 'name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'faculty')
	list_filter = ('faculty',)
	search_fields = ('code', 'name')


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
	list_display = ('name', 'start_date', 'end_date', 'is_active')
	list_filter = ('is_active',)
	search_fields = ('name',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
	list_display = ('academic_year', 'semester_num', 'start_date', 'end_date', 'is_active')
	list_filter = ('academic_year', 'is_active', 'semester_num')
