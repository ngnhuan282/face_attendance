from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from accounts.permissions import module_permission_required

from .forms import AcademicYearDateForm, SemesterForm
from .models import AcademicYear, Semester


def _sync_active_semester(semester):
    if not semester.is_active:
        return

    Semester.objects.exclude(pk=semester.pk).update(is_active=False)
    AcademicYear.objects.exclude(pk=semester.academic_year_id).update(is_active=False)
    AcademicYear.objects.filter(pk=semester.academic_year_id).update(is_active=True)


def _semester_query_params(request):
    return {
        'search_query': request.GET.get('q', '').strip(),
        'selected_year': request.GET.get('year', '').strip(),
    }


@module_permission_required('academics', 'view')
def semester_list(request):
    params = _semester_query_params(request)
    search_query = params['search_query']
    selected_year = params['selected_year']
    selected_academic_year = None

    semesters = (
        Semester.objects.select_related('academic_year')
        .annotate(course_class_count=Count('course_classes'))
        .order_by('-academic_year__start_date', 'semester_num')
    )

    if selected_year and selected_year.isdigit():
        selected_academic_year = AcademicYear.objects.filter(pk=selected_year).first()
        if selected_academic_year:
            semesters = semesters.filter(academic_year=selected_academic_year)
        else:
            selected_year = ''
    elif selected_year:
        selected_year = ''

    if search_query:
        search_filter = Q(academic_year__name__icontains=search_query)
        semester_part = search_query.upper().replace('HK', '').strip()
        if semester_part.isdigit():
            search_filter |= Q(semester_num=int(semester_part))
        semesters = semesters.filter(search_filter)

    paginator = Paginator(semesters, 10)
    page_number = request.GET.get('page', 1)
    if page_number in ('last', '999999'):
        page_number = paginator.num_pages
    page_obj = paginator.get_page(page_number)

    context = {
        'active_menu': 'academics',
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_year': selected_year,
        'selected_academic_year': selected_academic_year,
        'academic_years': AcademicYear.objects.order_by('-start_date'),
        'total_semesters': Semester.objects.count(),
        'academic_year_count': AcademicYear.objects.count(),
        'active_semester': (
            Semester.objects.select_related('academic_year')
            .filter(is_active=True)
            .order_by('-academic_year__start_date', '-semester_num')
            .first()
        ),
    }
    return render(request, 'academics/semester_list.html', context)


@module_permission_required('academics', 'edit')
@require_http_methods(['GET', 'POST'])
def academic_year_edit(request, pk):
    academic_year = get_object_or_404(AcademicYear, pk=pk)

    if request.method == 'POST':
        form = AcademicYearDateForm(request.POST, instance=academic_year)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cập nhật thời gian năm học {academic_year.name} thành công.')
            return redirect(f'{reverse("academics:semester_list")}?year={academic_year.pk}')
        messages.error(request, 'Vui lòng kiểm tra lại thời gian năm học.')
    else:
        form = AcademicYearDateForm(instance=academic_year)

    context = {
        'active_menu': 'academics',
        'form': form,
        'academic_year': academic_year,
        'form_title': f'Sửa Năm Học {academic_year.name}',
        'form_desc': 'Điều chỉnh ngày bắt đầu và ngày kết thúc của năm học. Khoảng này phải bao phủ các học kỳ hiện có.',
        'submit_label': 'Lưu Năm Học',
        'is_edit': True,
        'cancel_url': f'{reverse("academics:semester_list")}?year={academic_year.pk}',
    }
    return render(request, 'academics/semester_form.html', context)


@module_permission_required('academics', 'add')
@require_http_methods(['GET', 'POST'])
def semester_create(request):
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                semester = form.save()
                _sync_active_semester(semester)
            messages.success(request, f'Thêm học kỳ {semester} thành công.')
            return redirect('academics:semester_list')
        messages.error(request, 'Vui lòng kiểm tra lại thông tin học kỳ.')
    else:
        initial = {}
        year_id = request.GET.get('year', '').strip()
        if year_id.isdigit() and AcademicYear.objects.filter(pk=year_id).exists():
            initial['academic_year'] = year_id
        form = SemesterForm(initial=initial)

    context = {
        'active_menu': 'academics',
        'form': form,
        'form_title': 'Thêm Học Kỳ',
        'submit_label': 'Tạo Học Kỳ',
        'is_edit': False,
    }
    return render(request, 'academics/semester_form.html', context)


@module_permission_required('academics', 'edit')
@require_http_methods(['GET', 'POST'])
def semester_edit(request, pk):
    semester = get_object_or_404(Semester.objects.select_related('academic_year'), pk=pk)

    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            with transaction.atomic():
                semester = form.save()
                _sync_active_semester(semester)
            messages.success(request, f'Cập nhật học kỳ {semester} thành công.')
            return redirect('academics:semester_list')
        messages.error(request, 'Vui lòng kiểm tra lại thông tin học kỳ.')
    else:
        form = SemesterForm(instance=semester)

    context = {
        'active_menu': 'academics',
        'form': form,
        'semester': semester,
        'form_title': 'Sửa Học Kỳ',
        'submit_label': 'Lưu Thay Đổi',
        'is_edit': True,
    }
    return render(request, 'academics/semester_form.html', context)


@module_permission_required('academics', 'delete')
@require_http_methods(['POST'])
def semester_delete(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    semester_name = str(semester)
    was_active = semester.is_active

    if semester.course_classes.exists():
        messages.error(request, 'Không thể xóa học kỳ đang có lớp học phần.')
        return redirect('academics:semester_list')

    try:
        with transaction.atomic():
            semester.delete()
            if was_active:
                replacement = (
                    Semester.objects.select_related('academic_year')
                    .order_by('-academic_year__start_date', '-semester_num')
                    .first()
                )
                if replacement:
                    replacement.is_active = True
                    replacement.save(update_fields=['is_active'])
                    _sync_active_semester(replacement)
                else:
                    AcademicYear.objects.update(is_active=False)
        messages.success(request, f'Xóa học kỳ {semester_name} thành công.')
    except ProtectedError:
        messages.error(request, 'Không thể xóa học kỳ vì đang có dữ liệu liên kết.')

    return redirect('academics:semester_list')
