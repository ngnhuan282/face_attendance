from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required
from academics.models import Department

from .models import Student, StudentClass
from .forms import StudentForm, StudentClassForm


# ──────────────────────────────────────────────
# SINH VIÊN – CRUD
# ──────────────────────────────────────────────

@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def student_list(request):
    """Danh sách sinh viên – có tìm kiếm và lọc theo lớp / ngành."""
    qs = Student.objects.select_related('student_class', 'student_class__department')

    # Tìm kiếm
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(student_id__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q)
        )

    # Lọc theo lớp
    class_id = request.GET.get('class_id', '').strip()
    if class_id:
        qs = qs.filter(student_class_id=class_id)

    # Lọc theo ngành
    dept_id = request.GET.get('dept_id', '').strip()
    if dept_id:
        qs = qs.filter(student_class__department_id=dept_id)

    # Thống kê
    total = Student.objects.count()
    with_photo = Student.objects.exclude(photo='').exclude(photo__isnull=True).count()
    without_photo = total - with_photo
    class_count = StudentClass.objects.count()

    # Dữ liệu cho filter dropdowns
    all_classes = StudentClass.objects.select_related('department').order_by('class_code')
    all_departments = Department.objects.all().order_by('name')

    # Phân trang – 10 dòng / trang
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'students/list.html', {
        'active_menu': 'students',
        'students': page_obj,          # page_obj thay cho qs
        'page_obj': page_obj,
        'paginator': paginator,
        'q': q,
        'class_id': class_id,
        'dept_id': dept_id,
        'all_classes': all_classes,
        'all_departments': all_departments,
        # Stats
        'total': total,
        'with_photo': with_photo,
        'without_photo': without_photo,
        'class_count': class_count,
    })


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def student_create(request):
    """Thêm sinh viên mới (có upload ảnh khuôn mặt)."""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Đã thêm sinh viên {student.full_name} ({student.student_id}) thành công.')
            return redirect('students:list')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin. Có lỗi trong form.')
    else:
        form = StudentForm()

    return render(request, 'students/form.html', {
        'active_menu': 'students',
        'form': form,
        'form_title': 'Thêm Sinh Viên Mới',
        'submit_label': 'Thêm Sinh Viên',
        'cancel_url': 'students:list',
    })


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def student_edit(request, pk):
    """Sửa thông tin sinh viên."""
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật thông tin sinh viên {student.full_name}.')
            return redirect('students:list')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
    else:
        form = StudentForm(instance=student)

    return render(request, 'students/form.html', {
        'active_menu': 'students',
        'form': form,
        'student': student,
        'form_title': f'Sửa Sinh Viên — {student.full_name}',
        'submit_label': 'Lưu Thay Đổi',
        'cancel_url': 'students:list',
    })


@group_required(ADMIN_GROUP_NAME)
def student_delete(request, pk):
    """Xóa sinh viên (chỉ Admin)."""
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Đã xóa sinh viên {name}.')
        return redirect('students:list')

    return render(request, 'students/confirm_delete.html', {
        'active_menu': 'students',
        'object': student,
        'object_label': f'sinh viên "{student.full_name} ({student.student_id})"',
        'cancel_url': 'students:list',
    })


# ──────────────────────────────────────────────
# LỚP SINH HOẠT – CRUD
# ──────────────────────────────────────────────

@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def studentclass_list(request):
    """Danh sách lớp sinh hoạt."""
    qs = StudentClass.objects.select_related('department').annotate(
        student_count=Count('students')
    ).order_by('-intake_year', 'class_code')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(class_code__icontains=q) | Q(class_name__icontains=q)
        )

    return render(request, 'students/class_list.html', {
        'active_menu': 'students',
        'classes': qs,
        'q': q,
    })


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def studentclass_create(request):
    """Thêm lớp sinh hoạt."""
    if request.method == 'POST':
        form = StudentClassForm(request.POST)
        if form.is_valid():
            sc = form.save()
            messages.success(request, f'Đã tạo lớp {sc.class_code} thành công.')
            return redirect('students:class_list')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
    else:
        form = StudentClassForm()

    return render(request, 'students/form.html', {
        'active_menu': 'students',
        'form': form,
        'form_title': 'Thêm Lớp Sinh Hoạt',
        'submit_label': 'Tạo Lớp',
        'cancel_url': 'students:class_list',
    })


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def studentclass_edit(request, pk):
    """Sửa lớp sinh hoạt."""
    sc = get_object_or_404(StudentClass, pk=pk)

    if request.method == 'POST':
        form = StudentClassForm(request.POST, instance=sc)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật lớp {sc.class_code}.')
            return redirect('students:class_list')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
    else:
        form = StudentClassForm(instance=sc)

    return render(request, 'students/form.html', {
        'active_menu': 'students',
        'form': form,
        'sc': sc,
        'form_title': f'Sửa Lớp — {sc.class_code}',
        'submit_label': 'Lưu Thay Đổi',
        'cancel_url': 'students:class_list',
    })


@group_required(ADMIN_GROUP_NAME)
def studentclass_delete(request, pk):
    """Xóa lớp sinh hoạt (chỉ Admin, không xóa được nếu còn sinh viên)."""
    sc = get_object_or_404(StudentClass, pk=pk)

    if request.method == 'POST':
        if sc.students.exists():
            messages.error(request, f'Không thể xóa lớp {sc.class_code} vì còn {sc.students.count()} sinh viên trong lớp.')
            return redirect('students:class_list')
        code = sc.class_code
        sc.delete()
        messages.success(request, f'Đã xóa lớp {code}.')
        return redirect('students:class_list')

    return render(request, 'students/confirm_delete.html', {
        'active_menu': 'students',
        'object': sc,
        'object_label': f'lớp sinh hoạt "{sc.class_code} — {sc.class_name}"',
        'cancel_url': 'students:class_list',
    })


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def studentclass_detail(request, pk):
    """Xem danh sách sinh viên trong một lớp sinh hoạt."""
    sc = get_object_or_404(
        StudentClass.objects.select_related('department'),
        pk=pk
    )
    students = sc.students.order_by('full_name')

    return render(request, 'students/class_detail.html', {
        'active_menu': 'students',
        'sc': sc,
        'students': students,
    })
