from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.account_list, name='list'),
    path('create/', views.account_create, name='create'),
    path('<int:pk>/update/', views.account_edit, name='edit'),
    path('<int:pk>/delete/', views.account_delete, name='delete'),
    path('permissions/', views.permission_matrix, name='permissions'),
    # Hồ sơ cá nhân (cho cả Admin và GV)
    path('profile/', views.teacher_profile, name='profile'),
    # API kiểm tra phân quyền — dùng để test tích hợp
    path('api/check-permission/', views.api_check_permission, name='api_check_permission'),
    path('api/permissions/get/', views.api_get_permissions, name='api_get_permissions'),
    path('api/permissions/save/', views.api_save_permissions, name='api_save_permissions'),
]
