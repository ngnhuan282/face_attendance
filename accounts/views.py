from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from .permissions import group_required
from .models import Teacher
from .forms import AccountForm, AccountEditForm, TeacherProfileForm


@group_required(ADMIN_GROUP_NAME)
def account_list(request):
    """Trang quản lý tài khoản – chỉ Admin."""
    from django.db.models import Q
    from django.core.paginator import Paginator
    
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    
    users = User.objects.prefetch_related('groups', 'teacher', 'teacher__department').all().order_by('id')
    
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
        
    total_count = User.objects.count()
    admin_count = User.objects.filter(Q(is_superuser=True) | Q(groups__name=ADMIN_GROUP_NAME)).distinct().count()
    teacher_count = User.objects.filter(groups__name=TEACHER_GROUP_NAME).distinct().count()
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
        'active_count': active_count
    })


@group_required(ADMIN_GROUP_NAME)
def account_create(request):
    """Thêm tài khoản mới (Admin / Giảng viên) – chỉ Admin."""
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

                    # Assign Group
                    role = form.cleaned_data['role']
                    if role == 'admin':
                        group = Group.objects.get(name=ADMIN_GROUP_NAME)
                        user.groups.add(group)
                    elif role == 'teacher':
                        group = Group.objects.get(name=TEACHER_GROUP_NAME)
                        user.groups.add(group)
                        
                        # Create Teacher profile
                        Teacher.objects.create(
                            user=user,
                            department=form.cleaned_data['department'],
                            teacher_id=form.cleaned_data['teacher_id'],
                            phone=form.cleaned_data['phone'],
                            avatar=form.cleaned_data['avatar']
                        )
                    
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


@group_required(ADMIN_GROUP_NAME)
def account_edit(request, pk):
    """Chỉnh sửa tài khoản – chỉ Admin."""
    user = get_object_or_404(User, pk=pk)
    
    # Get current role
    is_teacher = hasattr(user, 'teacher')
    current_role = 'teacher' if is_teacher else 'admin'
    
    initial_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'role': current_role,
        'is_active': user.is_active,
    }
    
    if is_teacher and hasattr(user, 'teacher'):
        initial_data.update({
            'department': user.teacher.department,
            'teacher_id': user.teacher.teacher_id,
            'phone': user.teacher.phone,
            'avatar': user.teacher.avatar,
        })
        
    if request.method == 'POST':
        form = AccountEditForm(request.POST, request.FILES, user_instance=user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update User
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']
                    user.is_active = form.cleaned_data['is_active']
                    
                    new_password = form.cleaned_data['password']
                    if new_password:
                        user.set_password(new_password)
                        
                    user.save()
                    
                    # Update Role and Group
                    new_role = form.cleaned_data['role']
                    if new_role != current_role:
                        # Remove old groups
                        user.groups.clear()
                        # Add new group
                        new_group = Group.objects.get(name=ADMIN_GROUP_NAME if new_role == 'admin' else TEACHER_GROUP_NAME)
                        user.groups.add(new_group)
                        
                    # Handle Teacher Profile
                    if new_role == 'teacher':
                        teacher_profile, created = Teacher.objects.get_or_create(user=user, defaults={
                            'department': form.cleaned_data['department'],
                            'teacher_id': form.cleaned_data['teacher_id'],
                        })
                        teacher_profile.department = form.cleaned_data['department']
                        teacher_profile.teacher_id = form.cleaned_data['teacher_id']
                        teacher_profile.phone = form.cleaned_data['phone']
                        
                        if form.cleaned_data['avatar']:
                            teacher_profile.avatar = form.cleaned_data['avatar']
                        teacher_profile.save()
                    else:
                        # If changed to admin, delete old teacher profile if it exists
                        Teacher.objects.filter(user=user).delete()
                        
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


@group_required(ADMIN_GROUP_NAME)
@require_POST
def account_delete(request, pk):
    """Xóa tài khoản – chỉ Admin (AJAX)."""
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deleting oneself
    if user == request.user:
        return JsonResponse({'error': 'Bạn không thể tự xóa tài khoản của chính mình.'}, status=400)
        
    username = user.username
    user.delete()
    messages.success(request, f'Xóa tài khoản {username} thành công.')
    return JsonResponse({'success': True})


@group_required(ADMIN_GROUP_NAME)
def permission_matrix(request):
    """Trang phân quyền hệ thống – chỉ Admin."""
    return render(request, 'accounts/permissions.html', {'active_menu': 'permissions'})


@login_required
def teacher_profile(request):
    """Trang hồ sơ cá nhân — dành cho Giảng viên tự xem và cập nhật.

    Admin cũng có thể xem hồ sơ của mình ở đây.
    GV thấy thêm: danh sách lớp đang dạy.
    """
    user = request.user
    teacher = getattr(user, 'teacher', None)

    # Chuẩn bị dữ liệu ban đầu cho form
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
                    # Cập nhật User
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']

                    # Đổi mật khẩu nếu nhập
                    new_pw = form.cleaned_data.get('new_password')
                    if new_pw:
                        user.set_password(new_pw)
                        # Giữ session đang nhập sau khi đổi mật khẩu
                        update_session_auth_hash(request, user)

                    user.save()

                    # Cập nhật Teacher profile
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

    # Lấy danh sách lớp đang dạy (nếu là GV)
    teaching_classes = []
    if teacher:
        from courses.models import CourseClass
        teaching_classes = (
            CourseClass.objects
            .filter(teacher=teacher)
            .select_related('course', 'semester')
            .order_by('-semester__start_date', 'class_code')
        )

    # Thống kê role
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
    """API JSON — kiểm tra quyền của user hiện tại.

    Dùng để test tích hợp phân quyền toàn hệ thống.
    Trả về thông tin role và danh sách quyền theo module.

    GET /accounts/api/check-permission/
    Response: {
        "username": "...",
        "full_name": "...",
        "role": "admin" | "teacher" | "unknown",
        "is_admin": true/false,
        "is_teacher": true/false,
        "is_superuser": true/false,
        "groups": [...],
        "permissions": {
            "accounts": {"view": true, "add": true, "edit": true, "delete": true},
            "students": {...},
            ...
        }
    }
    """
    user = request.user
    is_admin = user.is_superuser or user.groups.filter(name=ADMIN_GROUP_NAME).exists()
    is_teacher = user.groups.filter(name=TEACHER_GROUP_NAME).exists()
    groups = list(user.groups.values_list('name', flat=True))

    # Xác định role chính
    if is_admin:
        role = 'admin'
    elif is_teacher:
        role = 'teacher'
    else:
        role = 'unknown'

    # Ma trận quyền theo module
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
    else:
        permissions = {}

    # Nếu là GV, thêm thông tin lớp đang dạy
    teaching_classes_info = []
    if is_teacher and not is_admin:
        teacher = getattr(user, 'teacher', None)
        if teacher:
            from courses.models import CourseClass
            qs = CourseClass.objects.filter(teacher=teacher).select_related('course', 'semester')
            teaching_classes_info = [
                {
                    'id': cc.id,
                    'class_code': cc.class_code,
                    'course_name': cc.course.course_name,
                    'semester': str(cc.semester),
                }
                for cc in qs
            ]

    return JsonResponse({
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'role': role,
        'is_admin': is_admin,
        'is_teacher': is_teacher,
        'is_superuser': user.is_superuser,
        'groups': groups,
        'permissions': permissions,
        'teaching_classes': teaching_classes_info,
        'note': (
            'GV chỉ được xem lớp mình dạy. '
            'Admin có toàn quyền trên tất cả module.'
        ),
    }, json_dumps_params={'ensure_ascii': False, 'indent': 2})
