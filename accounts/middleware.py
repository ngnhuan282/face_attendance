from __future__ import annotations

from django.http import HttpRequest

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME

STUDENT_GROUP_NAME = 'Student'


class RoleFlagsMiddleware:
    """Attach role flags for templates/views.

    We keep this middleware non-blocking (safe), and enforce access
    in views using `accounts.permissions.group_required`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        user = getattr(request, 'user', None)

        request.is_admin_group = False
        request.is_teacher_group = False
        request.is_student_group = False
        request.student_profile = None

        if user is not None and getattr(user, 'is_authenticated', False):
            if user.is_superuser:
                request.is_admin_group = True
                request.is_teacher_group = True
            else:
                qs = user.groups.all()
                request.is_admin_group = qs.filter(name=ADMIN_GROUP_NAME).exists()
                request.is_teacher_group = qs.filter(name=TEACHER_GROUP_NAME).exists()
                request.is_student_group = qs.filter(name=STUDENT_GROUP_NAME).exists()

            # Gắn student profile nếu có
            request.student_profile = getattr(user, 'student', None)

        return self.get_response(request)
