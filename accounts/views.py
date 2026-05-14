from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


@login_required
def account_list(request):
    """Trang quản lý tài khoản (UI tĩnh)."""
    return render(request, 'accounts/list.html', {'active_menu': 'accounts'})
