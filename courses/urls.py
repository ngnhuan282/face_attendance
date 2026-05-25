from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Courses
    path('', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Course Classes
    path('classes/', views.courseclass_list, name='courseclass_list'),
    path('classes/create/', views.courseclass_create, name='courseclass_create'),
    path('classes/<int:pk>/edit/', views.courseclass_edit, name='courseclass_edit'),
    path('classes/<int:pk>/delete/', views.courseclass_delete, name='courseclass_delete'),
    path('classes/<int:pk>/', views.courseclass_detail, name='courseclass_detail'),
    
    # Enrollments
    path('enrollments/', views.enrollment_all_list, name='enrollment_all_list'),
    path('classes/<int:courseclass_id>/enrollments/', views.enrollment_list, name='enrollment_list'),
    path('enrollments/add/', views.enrollment_add, name='enrollment_add'),
    path('enrollments/<int:enrollment_id>/remove/', views.enrollment_remove, name='enrollment_remove'),
    path('enrollments/export/', views.enrollment_export_all, name='enrollment_export_all'),
    path('enrollments/import/', views.enrollment_import_all, name='enrollment_import_all'),
    path('classes/<int:courseclass_id>/enrollments/import/', views.enrollment_import, name='enrollment_import'),
]
