from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required


def home(request):
    """Trang chủ giới thiệu hệ thống EduFace (public)."""
    return render(request, 'dashboards/home.html')


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def dashboard(request):
    """Dashboard chính – yêu cầu đăng nhập và phải thuộc 1 trong 2 nhóm."""
    return render(request, 'dashboards/dashboard.html', {'active_menu': 'dashboard'})
