from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # ── Sinh Viên ────────────────────────────────
    path('', views.student_list, name='list'),
    path('them/', views.student_create, name='create'),
    path('<int:pk>/sua/', views.student_edit, name='edit'),
    path('<int:pk>/xoa/', views.student_delete, name='delete'),

    # ── Lớp Sinh Hoạt ────────────────────────────
    path('lop/', views.studentclass_list, name='class_list'),
    path('lop/them/', views.studentclass_create, name='class_create'),
    path('lop/<int:pk>/', views.studentclass_detail, name='class_detail'),
    path('lop/<int:pk>/sua/', views.studentclass_edit, name='class_edit'),
    path('lop/<int:pk>/xoa/', views.studentclass_delete, name='class_delete'),
]
