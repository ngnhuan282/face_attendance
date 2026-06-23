from __future__ import annotations

from django.http import HttpRequest

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME, STUDENT_GROUP_NAME


# Default permissions (fallback nếu DB chưa có record)
_DEFAULT_PERMS = {
    'admin': {
        'dashboard':          {'view': True,  'add': False, 'edit': False, 'delete': False},
        'accounts':           {'view': True,  'add': True,  'edit': True,  'delete': True},
        'students':           {'view': True,  'add': True,  'edit': True,  'delete': True},
        'attendance':         {'view': True,  'add': True,  'edit': True,  'delete': True},
        'courses':            {'view': True,  'add': True,  'edit': True,  'delete': True},
        'schedules':          {'view': True,  'add': True,  'edit': True,  'delete': True},
        'academics':          {'view': True,  'add': True,  'edit': True,  'delete': True},
        'faculty_department': {'view': True,  'add': True,  'edit': True,  'delete': True},
        'reports':            {'view': True,  'add': True,  'edit': True,  'delete': True},
        'recognition':        {'view': True,  'add': True,  'edit': True,  'delete': True},
        'permissions':        {'view': True,  'add': True,  'edit': True,  'delete': True},
        'notifications':      {'view': True,  'add': True,  'edit': True,  'delete': True},
    },
    'teacher': {
        'dashboard':          {'view': False, 'add': False, 'edit': False, 'delete': False},
        'accounts':           {'view': False, 'add': False, 'edit': False, 'delete': False},
        'students':           {'view': False, 'add': False, 'edit': False, 'delete': False},
        'attendance':         {'view': True,  'add': True,  'edit': True,  'delete': False},
        'courses':            {'view': False, 'add': False, 'edit': False, 'delete': False},
        'schedules':          {'view': False, 'add': False, 'edit': False, 'delete': False},
        'academics':          {'view': False, 'add': False, 'edit': False, 'delete': False},
        'faculty_department': {'view': False, 'add': False, 'edit': False, 'delete': False},
        'reports':            {'view': False, 'add': False, 'edit': False, 'delete': False},
        'recognition':        {'view': True,  'add': False, 'edit': False, 'delete': False},
        'permissions':        {'view': False, 'add': False, 'edit': False, 'delete': False},
        'notifications':      {'view': True,  'add': True,  'edit': False, 'delete': False},
    },
}


def _get_role_perms(role: str) -> dict:
    """Lấy permissions từ DB, fallback về default nếu chưa có."""
    try:
        from .models import RolePermission
        rp = RolePermission.objects.filter(role=role).first()
        if rp and rp.permissions:
            # Merge với default để đảm bảo không thiếu module nào
            import copy
            merged = copy.deepcopy(_DEFAULT_PERMS.get(role, {}))
            for module, perms in rp.permissions.items():
                if module in merged:
                    merged[module].update(perms)
                else:
                    merged[module] = perms
            return merged
    except Exception:
        pass
    return _DEFAULT_PERMS.get(role, {})


class RoleFlagsMiddleware:
    """Attach role flags và permission flags cho templates/views.

    Đọc ma trận quyền từ DB (RolePermission) và gắn vào request:
    - request.is_admin_group / is_teacher_group / is_student_group
    - request.user_permissions  (dict toàn bộ quyền)
    - request.can_view_accounts, request.can_view_students, ... (shorthand flags)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        user = getattr(request, 'user', None)

        request.is_admin_group = False
        request.is_teacher_group = False
        request.is_student_group = False
        request.student_profile = None
        request.user_permissions = {}

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

            # Xác định role và load permissions từ DB
            if user.is_superuser or request.is_admin_group:
                # Admin: merge _DEFAULT_PERMS với DB (đảm bảo module mới luôn có)
                perms = _get_role_perms('admin')
            elif request.is_teacher_group:
                perms = _get_role_perms('teacher')
            else:
                perms = {}

            request.user_permissions = perms

            # Gắn shorthand flags tiện lợi cho templates
            def _can(module, action='view'):
                return perms.get(module, {}).get(action, False)

            request.can_view_dashboard          = _can('dashboard')
            request.can_view_accounts           = _can('accounts')
            request.can_view_students           = _can('students')
            request.can_view_attendance         = _can('attendance')
            request.can_view_courses            = _can('courses')
            request.can_view_schedules          = _can('schedules')
            request.can_view_academics          = _can('academics')
            request.can_view_faculty_department = _can('faculty_department')
            request.can_view_reports            = _can('reports')
            request.can_view_recognition        = _can('recognition')
            request.can_view_permissions        = _can('permissions')
            request.can_view_notifications      = _can('notifications')

            # Shorthand flags cho add/edit/delete (dùng trong templates)
            request.can_add_accounts      = _can('accounts', 'add')
            request.can_edit_accounts     = _can('accounts', 'edit')
            request.can_delete_accounts   = _can('accounts', 'delete')

            request.can_add_students      = _can('students', 'add')
            request.can_edit_students     = _can('students', 'edit')
            request.can_delete_students   = _can('students', 'delete')

            request.can_add_attendance    = _can('attendance', 'add')
            request.can_edit_attendance   = _can('attendance', 'edit')
            request.can_delete_attendance = _can('attendance', 'delete')

            request.can_add_courses       = _can('courses', 'add')
            request.can_edit_courses      = _can('courses', 'edit')
            request.can_delete_courses    = _can('courses', 'delete')

            request.can_add_schedules     = _can('schedules', 'add')
            request.can_edit_schedules    = _can('schedules', 'edit')
            request.can_delete_schedules  = _can('schedules', 'delete')

            request.can_add_academics     = _can('academics', 'add')
            request.can_edit_academics    = _can('academics', 'edit')
            request.can_delete_academics  = _can('academics', 'delete')

            request.can_add_faculty_department    = _can('faculty_department', 'add')
            request.can_edit_faculty_department   = _can('faculty_department', 'edit')
            request.can_delete_faculty_department = _can('faculty_department', 'delete')

            request.can_add_reports       = _can('reports', 'add')
            request.can_edit_reports      = _can('reports', 'edit')
            request.can_delete_reports    = _can('reports', 'delete')

        return self.get_response(request)
