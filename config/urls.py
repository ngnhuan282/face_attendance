"""
URL configuration for EduFace project.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from dashboards.views import home, dashboard

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Trang chủ (public)
    path('', home, name='home'),

    # Dashboard (yêu cầu đăng nhập)
    path('dashboard/', dashboard, name='dashboard'),

    # Quản lý tài khoản
    path('accounts/', include('accounts.urls')),

    # Quản lý sinh viên
    path('students/', include('students.urls')),
]