"""
URL configuration for EduFace project.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
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

    # Điểm danh
    path('attendance/', include('attendance.urls')),

    # Quản lý học phần
    path('courses/', include('courses.urls')),
    
    # Quản lý lịch học và phòng học
    path('schedules/', include('schedules.urls')),
    
    path('reports/', include('reports.urls')),
    
    path('notifications/', include('notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT if hasattr(settings, 'STATIC_ROOT') else None)
