from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # ── Students ─────────────────────────────────
    path('', views.student_list, name='list'),
    path('create/', views.student_create, name='create'),
    path('<int:pk>/update/', views.student_edit, name='edit'),
    path('<int:pk>/delete/', views.student_delete, name='delete'),

    # ── Student Classes ───────────────────────────
    path('classes/', views.studentclass_list, name='class_list'),
    path('classes/create/', views.studentclass_create, name='class_create'),
    path('classes/<int:pk>/', views.studentclass_detail, name='class_detail'),
    path('classes/<int:pk>/update/', views.studentclass_edit, name='class_edit'),
    path('classes/<int:pk>/delete/', views.studentclass_delete, name='class_delete'),
]
