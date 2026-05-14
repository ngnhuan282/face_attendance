from django.shortcuts import render


def home(request):
    """Trang chủ giới thiệu hệ thống EduFace."""
    return render(request, 'dashboards/home.html')
