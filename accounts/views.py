from django.shortcuts import render
from django.contrib.auth.models import User

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from .permissions import group_required


@group_required(ADMIN_GROUP_NAME)
def account_list(request):
    """Trang quản lý tài khoản – chỉ Admin."""
    return render(request, 'accounts/list.html', {'active_menu': 'accounts'})


@group_required(ADMIN_GROUP_NAME)
def permission_matrix(request):
    """Trang phân quyền hệ thống – chỉ Admin."""
    return render(request, 'accounts/permissions.html', {'active_menu': 'permissions'})
