
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from academics.models import Semester
from courses.models import CourseClass, Enrollment

from .models import AttendanceReport
from .services import refresh_class_reports



# View chọn lớp HP / học kỳ
@login_required
def report_index(request):
    semesters    = Semester.objects.all().order_by('-start_date')
    selected_sem = None
    course_classes = CourseClass.objects.none()

    sem_id = request.GET.get('semester')
    if sem_id:
        selected_sem   = get_object_or_404(Semester, pk=sem_id)
        course_classes = (
            CourseClass.objects
            .filter(semester=selected_sem)
            .select_related('course', 'teacher__user')
            .order_by('class_code')
        )

    context = {
        'semesters'      : semesters,
        'selected_sem'   : selected_sem,
        'course_classes' : course_classes,
        'active_menu'    : 'reports',
    }
    return render(request, 'reports/index.html', context)


@login_required
def report_class(request, class_id):
    course_class = get_object_or_404(
        CourseClass.objects.select_related('course', 'semester', 'teacher__user'),
        pk=class_id,
    )

    # Cho phép refresh thủ công
    if request.GET.get('refresh') == '1':
        refresh_class_reports(course_class)

    # Lấy báo cáo, kèm thông tin sinh viên
    reports = (
        AttendanceReport.objects
        .filter(course_class=course_class)
        .select_related('student__student_class')
        .order_by('student__full_name')
    )

    # Thống kê tổng hợp để hiển thị header
    total_students   = reports.count()
    good_count       = reports.filter(attendance_rate__gte=80).count()   # ≥ 80 %
    warning_count = reports.filter(
        absent_rate__gt=20, absent_rate__lt=40
    ).count()
    danger_count     = reports.filter(absent_rate__gte=40).count()

    avg_rate = 0.0
    if total_students:
        total_sum = sum(r.attendance_rate for r in reports)
        avg_rate  = round(total_sum / total_students, 1)

    context = {
        'course_class'   : course_class,
        'reports'        : reports,
        'total_students' : total_students,
        'good_count'     : good_count,
        'warning_count'  : warning_count,
        'danger_count'   : danger_count,
        'avg_rate'       : avg_rate,
        'active_menu'    : 'reports',
    }
    return render(request, 'reports/class_report.html', context)


@login_required
def export_class_report(request, class_id):
    import csv
    from django.http import HttpResponse

    course_class = get_object_or_404(
        CourseClass.objects.select_related('course', 'semester', 'teacher__user'),
        pk=class_id,
    )

    reports = (
        AttendanceReport.objects
        .filter(course_class=course_class)
        .select_related('student__student_class')
        .order_by('student__full_name')
    )

    response = HttpResponse(content_type='text/csv')
    filename = f"bao_cao_chuyen_can_{course_class.class_code}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Write BOM for Excel compatibility with UTF-8
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow([
        'Mã SV', 'Họ Tên', 'Lớp Sinh Hoạt', 'Tổng Buổi',
        'Có Mặt', 'Đi Trễ', 'Vắng', 'Tỉ Lệ Có Mặt (%)', 'Trạng Thái'
    ])

    for rpt in reports:
        absent_pct = rpt.absent_rate
        if absent_pct >= 40:
            status = 'Nguy Hiểm'
        elif absent_pct > 20:
            status = 'Cảnh Báo'
        else:
            status = 'Đạt'

        writer.writerow([
            rpt.student.student_id,
            rpt.student.full_name,
            rpt.student.student_class.class_code if rpt.student.student_class else '',
            rpt.total_sessions,
            rpt.present_count,
            rpt.late_count,
            rpt.absent_count,
            rpt.attendance_rate,
            status
        ])

    return response
