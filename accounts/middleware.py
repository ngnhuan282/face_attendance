from __future__ import annotations

from django.http import HttpRequest

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME


class RoleFlagsMiddleware:
    """Attach role flags for templates/views.

    Week 1 plan asks for Groups + middleware-based permission checks.
    We keep this middleware non-blocking (safe), and enforce access
    in views using `accounts.permissions.group_required`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        user = getattr(request, 'user', None)

        request.is_admin_group = False
        request.is_teacher_group = False

        if user is not None and getattr(user, 'is_authenticated', False):
            if user.is_superuser:
                request.is_admin_group = True
                request.is_teacher_group = True
            else:
                qs = user.groups.all()
                request.is_admin_group = qs.filter(name=ADMIN_GROUP_NAME).exists()
                request.is_teacher_group = qs.filter(name=TEACHER_GROUP_NAME).exists()

        return self.get_response(request)
