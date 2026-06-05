from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from .permissions import group_required
from .models import Teacher
from .forms import AccountForm, AccountEditForm


@group_required(ADMIN_GROUP_NAME)
def account_list(request):
    """Trang quản lý tài khoản – chỉ Admin."""
    from django.db.models import Q
    users = User.objects.prefetch_related('groups', 'teacher', 'teacher__department').all().order_by('id')
    
    total_count = users.count()
    admin_count = users.filter(Q(is_superuser=True) | Q(groups__name=ADMIN_GROUP_NAME)).distinct().count()
    teacher_count = users.filter(groups__name=TEACHER_GROUP_NAME).distinct().count()
    active_count = users.filter(is_active=True).count()
    
    return render(request, 'accounts/list.html', {
        'active_menu': 'accounts',
        'users': users,
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

