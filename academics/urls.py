from django.urls import path

from . import views

app_name = 'academics'

urlpatterns = [
    path('', views.semester_list, name='semester_list'),
    # Faculty (Khoa)
    path('faculties/', views.faculty_list, name='faculty_list'),
    path('faculties/create/', views.faculty_create, name='faculty_create'),
    path('faculties/<int:pk>/edit/', views.faculty_edit, name='faculty_edit'),
    path('faculties/<int:pk>/delete/', views.faculty_delete, name='faculty_delete'),
    # Department (Ngành)
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    # Academic Year
    path('years/', views.academic_year_list, name='academic_year_list'),
    path('years/create/', views.academic_year_create, name='academic_year_create'),
    path('years/<int:pk>/edit/', views.academic_year_edit, name='academic_year_edit'),
    path('years/<int:pk>/delete/', views.academic_year_delete, name='academic_year_delete'),
    path('semesters/', views.semester_list, name='semester_list'),
    path('academic-years/<int:pk>/edit/', views.academic_year_edit, name='academic_year_edit_legacy'),
    path('semesters/create/', views.semester_create, name='semester_create'),
    path('semesters/<int:pk>/edit/', views.semester_edit, name='semester_edit'),
    path('semesters/<int:pk>/delete/', views.semester_delete, name='semester_delete'),
]
