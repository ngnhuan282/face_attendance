from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # ── Student Profile (self-service) ───────────
    path('profile/', views.student_profile, name='student_profile'),
    path('timetable/', views.student_timetable, name='timetable'),
    path('attendance-history/', views.student_attendance_history, name='attendance_history'),

    # ── Students ─────────────────────────────────
    path('', views.student_list, name='list'),
    path('create/', views.student_create, name='create'),
    path('<int:pk>/', views.student_detail, name='detail'),
    path('<int:pk>/update/', views.student_edit, name='edit'),
    path('<int:pk>/delete/', views.student_delete, name='delete'),
    # Import CSV hàng loạt (Admin)
    path('import-csv/', views.student_import_csv, name='import_csv'),
    path('import-csv/template/', views.student_import_csv_template, name='import_csv_template'),
    path('export-excel/', views.student_export_excel, name='export_excel'),

    # ── Student Classes ───────────────────────────
    path('classes/', views.studentclass_list, name='class_list'),
    path('classes/create/', views.studentclass_create, name='class_create'),
    path('classes/<int:pk>/', views.studentclass_detail, name='class_detail'),
    path('classes/<int:pk>/add-student/', views.studentclass_add_student, name='class_add_student'),
    path('classes/remove-student/<int:pk>/', views.studentclass_remove_student, name='class_remove_student'),
    path('classes/<int:pk>/update/', views.studentclass_edit, name='class_edit'),
    path('classes/<int:pk>/delete/', views.studentclass_delete, name='class_delete'),
]
