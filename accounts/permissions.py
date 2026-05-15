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
