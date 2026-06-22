from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME, STUDENT_GROUP_NAME
from .permissions import group_required, module_permission_required
from .models import Teacher
from .forms import AccountForm, AccountEditForm, TeacherProfileForm


@module_permission_required('accounts', 'view')
def account_list(request):
    """Trang quản lý tài khoản – chỉ Admin."""
    from django.db.models import Q
    from django.core.paginator import Paginator

    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()

    users = User.objects.prefetch_related(
        'groups', 'teacher', 'teacher__department', 'student', 'student__student_class'
    ).all().order_by('id')

    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )

    if role == 'admin':
        users = users.filter(Q(is_superuser=True) | Q(groups__name=ADMIN_GROUP_NAME)).distinct()
    elif role == 'teacher':
        users = users.filter(groups__name=TEACHER_GROUP_NAME).distinct()
    elif role == 'student':
        users = users.filter(groups__name=STUDENT_GROUP_NAME).distinct()

    total_count = User.objects.count()
    admin_count = User.objects.filter(
        Q(is_superuser=True) | Q(groups__name=ADMIN_GROUP_NAME)
    ).distinct().count()
    teacher_count = User.objects.filter(groups__name=TEACHER_GROUP_NAME).distinct().count()
    student_count = User.objects.filter(groups__name=STUDENT_GROUP_NAME).distinct().count()
    active_count = User.objects.filter(is_active=True).count()

    # Pagination - 10 rows / page
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/list.html', {
        'active_menu': 'accounts',
        'users': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'q': q,
        'role': role,
        'total_count': total_count,
        'admin_count': admin_count,
        'teacher_count': teacher_count,
        'student_count': student_count,
        'active_count': active_count,
    })


@module_permission_required('accounts', 'add')
def account_create(request):
    """Thêm tài khoản mới (Admin / Giảng viên / Sinh viên) – chỉ Admin."""
    if request.method == 'POST':
        form = AccountForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create User
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        password=form.cleaned_data['password'],
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name']
                    )
                    user.is_active = form.cleaned_data['is_active']
                    user.save()

                    # Assign Group and create profile
                    role = form.cleaned_data['role']

                    if role == 'admin':
                        group = Group.objects.get(name=ADMIN_GROUP_NAME)
                        user.groups.add(group)

                    elif role == 'teacher':
                        group = Group.objects.get(name=TEACHER_GROUP_NAME)
                        user.groups.add(group)
                        Teacher.objects.create(
                            user=user,
                            department=form.cleaned_data['department'],
                            teacher_id=form.cleaned_data['teacher_id'],
                            phone=form.cleaned_data['phone'],
                            avatar=form.cleaned_data['avatar']
                        )

                    elif role == 'student':
                        group, _ = Group.objects.get_or_create(name=STUDENT_GROUP_NAME)
                        user.groups.add(group)
                        # Link to existing Student record
                        from students.models import Student
                        student = Student.objects.get(
                            student_id=form.cleaned_data['student_id_link'].strip()
                        )
                        student.user = user
                        student.save(update_fields=['user'])

                    messages.success(request, f'Tạo tài khoản {user.username} thành công.')
                    return redirect('accounts:list')
            except Exception as e:
                form.add_error(None, f'Đã xảy ra lỗi: {str(e)}')
    else:
        form = AccountForm()

    return render(request, 'accounts/form.html', {
        'active_menu': 'accounts',
        'form': form,
        'form_title': 'Thêm Tài Khoản',
        'submit_label': 'Tạo Tài Khoản',
        'cancel_url': 'accounts:list',
    })


@module_permission_required('accounts', 'edit')
def account_edit(request, pk):
    """Chỉnh sửa tài khoản – chỉ Admin."""
    user = get_object_or_404(User, pk=pk)

    # Detect current role
    is_student = user.groups.filter(name=STUDENT_GROUP_NAME).exists()
    is_teacher = not is_student and hasattr(user, 'teacher') and user.teacher is not None
    if is_student:
        current_role = 'student'
    elif is_teacher:
        current_role = 'teacher'
    else:
        current_role = 'admin'

    initial_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'role': current_role,
        'is_active': user.is_active,
    }

    if is_teacher:
        initial_data.update({
            'department': user.teacher.department,
            'teacher_id': user.teacher.teacher_id,
            'phone': user.teacher.phone,
        })
    elif is_student:
        student = getattr(user, 'student', None)
        if student:
            initial_data['student_id_link'] = student.student_id

    if request.method == 'POST':
        form = AccountEditForm(request.POST, request.FILES, user_instance=user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update User base fields
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']
                    user.is_active = form.cleaned_data['is_active']

                    new_password = form.cleaned_data['password']
                    if new_password:
                        user.set_password(new_password)
                    user.save()

                    new_role = form.cleaned_data['role']

                    # Always clear groups first, then re-assign
                    user.groups.clear()

                    if new_role == 'admin':
                        group = Group.objects.get(name=ADMIN_GROUP_NAME)
                        user.groups.add(group)
                        # Remove old teacher profile if any
                        Teacher.objects.filter(user=user).delete()
                        # Unlink student if was linked
                        _unlink_student(user)

                    elif new_role == 'teacher':
                        group = Group.objects.get(name=TEACHER_GROUP_NAME)
                        user.groups.add(group)
                        # Unlink student if switching from student
                        _unlink_student(user)
                        # Create/update teacher profile
                        teacher_profile, _ = Teacher.objects.get_or_create(
                            user=user,
                            defaults={
                                'department': form.cleaned_data['department'],
                                'teacher_id': form.cleaned_data['teacher_id'],
                            }
                        )
                        teacher_profile.department = form.cleaned_data['department']
                        teacher_profile.teacher_id = form.cleaned_data['teacher_id']
                        teacher_profile.phone = form.cleaned_data['phone']
                        if form.cleaned_data['avatar']:
                            teacher_profile.avatar = form.cleaned_data['avatar']
                        teacher_profile.save()

                    elif new_role == 'student':
                        group, _ = Group.objects.get_or_create(name=STUDENT_GROUP_NAME)
                        user.groups.add(group)
                        # Remove teacher profile if any
                        Teacher.objects.filter(user=user).delete()
                        # Unlink old student, then link new one
                        _unlink_student(user)
                        from students.models import Student
                        student = Student.objects.get(
                            student_id=form.cleaned_data['student_id_link'].strip()
                        )
                        student.user = user
                        student.save(update_fields=['user'])

                    messages.success(request, f'Cập nhật tài khoản {user.username} thành công.')
                    return redirect('accounts:list')
            except Exception as e:
                form.add_error(None, f'Đã xảy ra lỗi: {str(e)}')
    else:
        form = AccountEditForm(initial=initial_data, user_instance=user)

    return render(request, 'accounts/form.html', {
        'active_menu': 'accounts',
        'form': form,
        'user_instance': user,
        'form_title': f'Sửa Tài Khoản — {user.username}',
        'submit_label': 'Lưu Thay Đổi',
        'cancel_url': 'accounts:list',
    })


def _unlink_student(user):
    """Bỏ liên kết student.user nếu có."""
    from students.models import Student
    Student.objects.filter(user=user).update(user=None)


@module_permission_required('accounts', 'delete')
@require_POST
def account_delete(request, pk):
    """Xóa tài khoản – chỉ Admin (AJAX)."""
    from django.db.models import ProtectedError
    user = get_object_or_404(User, pk=pk)

    if user == request.user:
        return JsonResponse({'error': 'Bạn không thể tự xóa tài khoản của chính mình.'}, status=400)

    # Unlink student record before deleting user (SET_NULL will handle it but be explicit)
    from students.models import Student
    Student.objects.filter(user=user).update(user=None)

    username = user.username
    try:
        user.delete()
        messages.success(request, f'Xóa tài khoản {username} thành công.')
        return JsonResponse({'success': True})
    except ProtectedError as e:
        # Gather related objects that are blocking deletion
        blocked_by = []
        for obj in e.protected_objects:
            blocked_by.append(str(obj))

        if blocked_by:
            detail = '; '.join(blocked_by[:5])
            if len(blocked_by) > 5:
                detail += f' … và {len(blocked_by) - 5} mục khác'
            msg = (
                f'Không thể xóa tài khoản <strong>{username}</strong> vì giảng viên này '
                f'đang phụ trách {len(blocked_by)} lớp học phần. '
                f'Vui lòng gán giảng viên khác cho các lớp trước khi xóa.<br>'
                f'<small style="opacity:.75">Lớp liên quan: {detail}</small>'
            )
        else:
            msg = f'Không thể xóa tài khoản {username} vì dữ liệu đang được tham chiếu ở nơi khác.'

        return JsonResponse({'error': msg, 'html': True}, status=409)


@group_required(ADMIN_GROUP_NAME)
def permission_matrix(request):
    """Trang phân quyền hệ thống – chỉ Admin."""
    return render(request, 'accounts/permissions.html', {'active_menu': 'permissions'})


# Default permissions used as fallback when DB has no record yet
_DEFAULT_PERMS = {
    'admin': {
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
        'accounts':           {'view': False, 'add': False, 'edit': False, 'delete': False},
        'students':           {'view': True,  'add': False, 'edit': True,  'delete': False},
        'attendance':         {'view': True,  'add': True,  'edit': True,  'delete': False},
        'courses':            {'view': True,  'add': False, 'edit': False, 'delete': False},
        'schedules':          {'view': True,  'add': False, 'edit': False, 'delete': False},
        'academics':          {'view': True,  'add': False, 'edit': False, 'delete': False},
        'faculty_department': {'view': True,  'add': False, 'edit': False, 'delete': False},
        'reports':            {'view': True,  'add': False, 'edit': False, 'delete': False},
        'recognition':        {'view': True,  'add': False, 'edit': False, 'delete': False},
        'permissions':        {'view': False, 'add': False, 'edit': False, 'delete': False},
        'notifications':      {'view': True,  'add': True,  'edit': False, 'delete': False},
    },
}


@group_required(ADMIN_GROUP_NAME)
def api_get_permissions(request):
    """API GET – Trả về ma trận quyền hiện tại cho tất cả role."""
    from .models import RolePermission
    import copy
    # Bắt đầu từ default (bao gồm module mới như faculty_department)
    result = copy.deepcopy(_DEFAULT_PERMS)
    # Merge với DB: module có trong DB sẽ ghi đè default
    for rp in RolePermission.objects.all():
        if rp.role in result and rp.permissions:
            for module, perms in rp.permissions.items():
                if module in result[rp.role]:
                    result[rp.role][module].update(perms)
                else:
                    result[rp.role][module] = perms
    return JsonResponse({'permissions': result}, json_dumps_params={'ensure_ascii': False})


@group_required(ADMIN_GROUP_NAME)
@require_POST
def api_save_permissions(request):
    """API POST – Lưu ma trận quyền cho một role vào DB."""
    import json
    from .models import RolePermission
    try:
        data = json.loads(request.body)
        role = data.get('role')
        permissions = data.get('permissions')

        if role not in ('admin', 'teacher'):
            return JsonResponse({'error': 'Role không hợp lệ.'}, status=400)

        if not isinstance(permissions, dict):
            return JsonResponse({'error': 'Dữ liệu quyền không hợp lệ.'}, status=400)

        # Validate structure: each module must have view/add/edit/delete booleans
        for module_id, perms in permissions.items():
            if not isinstance(perms, dict):
                return JsonResponse({'error': f'Module {module_id} có dữ liệu không hợp lệ.'}, status=400)
            for action in ('view', 'add', 'edit', 'delete'):
                if action not in perms or not isinstance(perms[action], bool):
                    return JsonResponse({'error': f'Module {module_id} thiếu hoặc sai kiểu action {action}.'}, status=400)

        RolePermission.objects.update_or_create(
            role=role,
            defaults={'permissions': permissions},
        )
        return JsonResponse({'success': True, 'role': role})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def teacher_profile(request):
    """Trang hồ sơ cá nhân — dành cho Giảng viên tự xem và cập nhật.

    Admin cũng có thể xem hồ sơ của mình ở đây.
    GV thấy thêm: danh sách lớp đang dạy.
    """
    user = request.user
    teacher = getattr(user, 'teacher', None)

    initial = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': teacher.phone if teacher else '',
    }

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES,
                                  user_instance=user, initial=initial)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']

                    new_pw = form.cleaned_data.get('new_password')
                    if new_pw:
                        user.set_password(new_pw)
                        update_session_auth_hash(request, user)

                    user.save()

                    if teacher:
                        teacher.phone = form.cleaned_data.get('phone', '')
                        new_avatar = form.cleaned_data.get('avatar')
                        if new_avatar:
                            teacher.avatar = new_avatar
                        teacher.save()

                messages.success(request, 'Cập nhật hồ sơ thành công!')
                return redirect('accounts:profile')
            except Exception as e:
                form.add_error(None, f'Đã xảy ra lỗi: {str(e)}')
    else:
        form = TeacherProfileForm(initial=initial, user_instance=user)

    teaching_classes = []
    if teacher:
        from courses.models import CourseClass
        teaching_classes = (
            CourseClass.objects
            .filter(teacher=teacher)
            .select_related('course', 'semester')
            .order_by('-semester__start_date', 'class_code')
        )

    is_admin = user.is_superuser or user.groups.filter(name=ADMIN_GROUP_NAME).exists()
    is_teacher = user.groups.filter(name=TEACHER_GROUP_NAME).exists()

    context = {
        'active_menu': 'profile',
        'form': form,
        'teacher': teacher,
        'teaching_classes': teaching_classes,
        'is_admin': is_admin,
        'is_teacher_role': is_teacher,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def api_check_permission(request):
    """API JSON — kiểm tra quyền của user hiện tại."""
    user = request.user
    is_admin = user.is_superuser or user.groups.filter(name=ADMIN_GROUP_NAME).exists()
    is_teacher = user.groups.filter(name=TEACHER_GROUP_NAME).exists()
    is_student = user.groups.filter(name=STUDENT_GROUP_NAME).exists()
    groups = list(user.groups.values_list('name', flat=True))

    if is_admin:
        role = 'admin'
    elif is_teacher:
        role = 'teacher'
    elif is_student:
        role = 'student'
    else:
        role = 'unknown'

    if is_admin:
        permissions = {
            'accounts':      {'view': True,  'add': True,  'edit': True,  'delete': True},
            'students':      {'view': True,  'add': True,  'edit': True,  'delete': True},
            'attendance':    {'view': True,  'add': True,  'edit': True,  'delete': True},
            'courses':       {'view': True,  'add': True,  'edit': True,  'delete': True},
            'schedules':     {'view': True,  'add': True,  'edit': True,  'delete': True},
            'academics':     {'view': True,  'add': True,  'edit': True,  'delete': True},
            'reports':       {'view': True,  'add': True,  'edit': True,  'delete': True},
            'notifications': {'view': True,  'add': True,  'edit': True,  'delete': True},
            'permissions':   {'view': True,  'add': True,  'edit': True,  'delete': True},
        }
    elif is_teacher:
        permissions = {
            'accounts':      {'view': False, 'add': False, 'edit': False, 'delete': False},
            'students':      {'view': True,  'add': False, 'edit': True,  'delete': False},
            'attendance':    {'view': True,  'add': True,  'edit': True,  'delete': False},
            'courses':       {'view': True,  'add': False, 'edit': False, 'delete': False},
            'schedules':     {'view': True,  'add': False, 'edit': False, 'delete': False},
            'academics':     {'view': True,  'add': False, 'edit': False, 'delete': False},
            'reports':       {'view': True,  'add': False, 'edit': False, 'delete': False},
            'notifications': {'view': True,  'add': True,  'edit': False, 'delete': False},
            'permissions':   {'view': False, 'add': False, 'edit': False, 'delete': False},
        }
    elif is_student:
        permissions = {
            'profile':       {'view': True,  'add': False, 'edit': True,  'delete': False},
            'attendance':    {'view': True,  'add': False, 'edit': False, 'delete': False},
        }
    else:
        permissions = {}

    return JsonResponse({
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'role': role,
        'is_admin': is_admin,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'is_superuser': user.is_superuser,
        'groups': groups,
        'permissions': permissions,
    }, json_dumps_params={'ensure_ascii': False, 'indent': 2})
