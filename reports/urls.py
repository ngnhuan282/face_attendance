from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_index, name='index'),
    path('class/<int:class_id>/', views.report_class, name='class'),
    path('class/<int:class_id>/excel/', views.export_excel, name='excel'),
    path('student/<int:student_id>/', views.student_attendance, name='student'),
    path('record/<int:session_id>/<int:student_id>/edit/', views.attendance_edit, name='record_edit'),
]
