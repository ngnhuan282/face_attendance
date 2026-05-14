from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    """Trang chủ giới thiệu hệ thống EduFace (public)."""
    return render(request, 'dashboards/home.html')


@login_required
def dashboard(request):
    """Dashboard chính sau khi đăng nhập."""
    return render(request, 'dashboards/dashboard.html', {'active_menu': 'dashboard'})
