from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required


def home(request):
    """Trang chủ giới thiệu hệ thống EduFace (public)."""
    return render(request, 'dashboards/home.html')


@login_required
def dashboard(request):
    """Dashboard chính – yêu cầu đăng nhập.

    - Admin / Giảng viên → hiển thị dashboard quản lý.
    - Sinh viên → redirect sang trang hồ sơ sinh viên.
    - Người dùng khác không có profile → báo lỗi hoặc redirect login.
    """
    user = request.user

    # Sinh viên → chuyển về trang hồ sơ sinh viên
    if hasattr(user, 'student') and user.student is not None:
        return redirect('students:student_profile')

    # Admin hoặc Giảng viên → hiển thị dashboard
    if request.is_admin_group or request.is_teacher_group:
        return render(request, 'dashboards/dashboard.html', {'active_menu': 'dashboard'})

    # Không thuộc nhóm nào → redirect login
    return redirect('login')
