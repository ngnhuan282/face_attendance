from __future__ import annotations

from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


P = ParamSpec('P')
R = TypeVar('R')


def group_required(*group_names: str):
    """Require the logged-in user to be in at least one Django Group.

    This complements Week 1's "Groups phan quyen" work. Use on views.
    """

    def decorator(view_func: Callable[P, R]) -> Callable[P, R]:
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args: P.args, **kwargs: P.kwargs):
            user = request.user
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not group_names:
                raise PermissionDenied

            if user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return _wrapped

    return decorator


def module_permission_required(module: str, action: str = 'view'):
    """Kiểm tra quyền theo module + action từ DB (RolePermission).

    Admin (is_superuser hoặc is_admin_group) luôn được phép.
    Các role khác kiểm tra flag request.can_view_* do middleware gắn vào.
    Dùng để bảo vệ view theo đúng phân quyền DB thay vì chỉ check Group.
    """
    def decorator(view_func: Callable[P, R]) -> Callable[P, R]:
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args: P.args, **kwargs: P.kwargs):
            user = request.user
            # Superuser và Admin Group luôn được qua
            if user.is_superuser or getattr(request, 'is_admin_group', False):
                return view_func(request, *args, **kwargs)

            # Kiểm tra qua flag được middleware gắn vào request
            flag_name = f'can_{action}_{module}'
            if getattr(request, flag_name, False):
                return view_func(request, *args, **kwargs)

            # Fallback: kiểm tra trực tiếp từ user_permissions dict
            perms = getattr(request, 'user_permissions', {})
            if perms.get(module, {}).get(action, False):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return _wrapped

    return decorator
