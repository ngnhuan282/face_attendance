"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from dashboards.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Login URL
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    # Logout URL (tự động có khi dùng auth_views)
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Trang chủ
    path('', home, name='home'),
    
    # ========================
    # Thêm các URL của app sau này ở đây
    # ========================
    # path('students/', include('students.urls')),
    # path('attendance/', include('attendance.urls')),
    # path('accounts/', include('accounts.urls')),
]