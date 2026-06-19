from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.permissions import module_permission_required

from .forms import AcademicYearForm, SemesterForm
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


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _form_error_message(form):
    messages_list = []
    for field_name, field_errors in form.errors.items():
        field_label = form.fields[field_name].label if field_name in form.fields else ''
        for error in field_errors:
            messages_list.append(f'{field_label}: {error}' if field_label else str(error))
    return '\n'.join(messages_list) or 'Vui lòng kiểm tra lại thông tin.'


def _ajax_form_error(form):
    return JsonResponse(
        {
            'success': False,
            'error': _form_error_message(form),
            'errors': form.errors.get_json_data(),
        },
        status=400,
    )


@module_permission_required('academics', 'view')
def academic_year_list(request):
    search_query = request.GET.get('q', '').strip()

    academic_years = (
        AcademicYear.objects
        .annotate(
            semester_count=Count('semesters', distinct=True),
            course_class_count=Count('semesters__course_classes', distinct=True),
        )
        .order_by('-start_date')
    )

    if search_query:
        academic_years = academic_years.filter(name__icontains=search_query)

    paginator = Paginator(academic_years, 10)
    page_number = request.GET.get('page', 1)
    if page_number in ('last', '999999'):
        page_number = paginator.num_pages
    page_obj = paginator.get_page(page_number)

    context = {
        'active_menu': 'academic_years',
        'page_obj': page_obj,
        'search_query': search_query,
        'total_years': AcademicYear.objects.count(),
        'total_semesters': Semester.objects.count(),
    }
    return render(request, 'academics/academic_year_list.html', context)


@module_permission_required('academics', 'add')
@require_http_methods(['GET', 'POST'])
def academic_year_create(request):
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            academic_year = form.save()
            if _is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': f'Thêm năm học {academic_year.name} thành công.',
                })
            messages.success(request, f'Thêm năm học {academic_year.name} thành công.')
            return redirect('academics:academic_year_list')
        if _is_ajax(request):
            return _ajax_form_error(form)
        messages.error(request, 'Vui lòng kiểm tra lại thông tin năm học.')
    else:
        form = AcademicYearForm()

    context = {
        'active_menu': 'academic_years',
        'form': form,
        'form_title': 'Thêm Năm Học',
        'submit_label': 'Tạo Năm Học',
        'is_edit': False,
    }
    return render(request, 'academics/academic_year_form.html', context)


@module_permission_required('academics', 'edit')
@require_http_methods(['GET', 'POST'])
def academic_year_edit(request, pk):
    academic_year = get_object_or_404(AcademicYear, pk=pk)

    if request.method == 'POST':
        form = AcademicYearForm(request.POST, instance=academic_year)
        if form.is_valid():
            academic_year = form.save()
            if _is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': f'Cập nhật năm học {academic_year.name} thành công.',
                })
            messages.success(request, f'Cập nhật năm học {academic_year.name} thành công.')
            return redirect('academics:academic_year_list')
        if _is_ajax(request):
            return _ajax_form_error(form)
        messages.error(request, 'Vui lòng kiểm tra lại thông tin năm học.')
    else:
        form = AcademicYearForm(instance=academic_year)

    context = {
        'active_menu': 'academic_years',
        'form': form,
        'academic_year': academic_year,
        'form_title': f'Sửa Năm Học {academic_year.name}',
        'submit_label': 'Lưu Thay Đổi',
        'is_edit': True,
    }
    return render(request, 'academics/academic_year_form.html', context)


@module_permission_required('academics', 'delete')
@require_http_methods(['POST'])
def academic_year_delete(request, pk):
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    year_name = academic_year.name

    if academic_year.semesters.exists():
        messages.error(request, 'Không thể xóa năm học đang có học kỳ.')
        return redirect('academics:academic_year_list')

    try:
        academic_year.delete()
        messages.success(request, f'Xóa năm học {year_name} thành công.')
    except ProtectedError:
        messages.error(request, 'Không thể xóa năm học vì đang có dữ liệu liên kết.')

    return redirect('academics:academic_year_list')


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
        'active_menu': 'semesters',
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


@module_permission_required('academics', 'add')
@require_http_methods(['GET', 'POST'])
def semester_create(request):
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                semester = form.save()
                _sync_active_semester(semester)
            if _is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': f'Thêm học kỳ {semester} thành công.',
                })
            messages.success(request, f'Thêm học kỳ {semester} thành công.')
            return redirect('academics:semester_list')
        if _is_ajax(request):
            return _ajax_form_error(form)
        messages.error(request, 'Vui lòng kiểm tra lại thông tin học kỳ.')
    else:
        initial = {}
        year_id = request.GET.get('year', '').strip()
        if year_id.isdigit() and AcademicYear.objects.filter(pk=year_id).exists():
            initial['academic_year'] = year_id
        form = SemesterForm(initial=initial)

    context = {
        'active_menu': 'semesters',
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
            if _is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': f'Cập nhật học kỳ {semester} thành công.',
                })
            messages.success(request, f'Cập nhật học kỳ {semester} thành công.')
            return redirect('academics:semester_list')
        if _is_ajax(request):
            return _ajax_form_error(form)
        messages.error(request, 'Vui lòng kiểm tra lại thông tin học kỳ.')
    else:
        form = SemesterForm(instance=semester)

    context = {
        'active_menu': 'semesters',
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
