from django.shortcuts import render
from django.contrib.auth.models import User

from .constants import ADMIN_GROUP_NAME
from .permissions import group_required


@group_required(ADMIN_GROUP_NAME)
def account_list(request):
    """Trang quản lý tài khoản (UI tĩnh)."""
    return render(request, 'accounts/list.html', {'active_menu': 'accounts'})
