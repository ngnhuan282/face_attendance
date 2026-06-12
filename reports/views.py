from __future__ import annotations

import io
from datetime import datetime

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required
from academics.models import Semester
from attendance.models import AttendanceRecord, AttendanceSession
from courses.models import CourseClass, Enrollment
from students.models import Student

from .models import AttendanceReport
from .services import refresh_class_reports



def _build_session_columns(course_class: CourseClass):
    return list(
        AttendanceSession.objects.filter(
            course_class=course_class,
            status='closed',
        ).order_by('started_at')
    )


def _build_matrix(reports, sessions):
    session_ids = [s.pk for s in sessions]
    student_ids = [r.student_id for r in reports]

    # Lấy tất cả record
    records = AttendanceRecord.objects.filter(
        session_id__in=session_ids,
        student__in=student_ids,
    ).values('session_id', 'student_id', 'status')

    # Index: (session_id, student_id) → status
    rec_map = {(r['session_id'], r['student_id']): r['status'] for r in records}

    # Fetch enrollments to know when each student enrolled
    course_class_id = sessions[0].course_class_id if sessions else None
    enrollments = {}
    if course_class_id:
        enr_list = Enrollment.objects.filter(
            course_class_id=course_class_id,
            student_id__in=student_ids,
            is_active=True,
        ).values('student_id', 'enrolled_at')
        enrollments = {e['student_id']: e['enrolled_at'].date() for e in enr_list}

    rows = []
    for rpt in reports:
        enrolled_date = enrollments.get(rpt.student_id)
        cells = []
        for s in sessions:
            # Nếu buổi học diễn ra trước khi SV đăng ký, không tính vắng
            if enrolled_date and s.started_at.date() < enrolled_date:
                cells.append('not_enrolled')
            else:
                cells.append(rec_map.get((s.pk, rpt.student_id), 'absent'))
        rows.append({'report': rpt, 'cells': cells})
    return rows


def _get_active_reports(course_class: CourseClass):
    return (
        AttendanceReport.objects
        .filter(
            course_class=course_class,
            student__enrollments__course_class=course_class,
            student__enrollments__is_active=True,
        )
        .select_related('student__student_class')
        .order_by('student__full_name')
        .distinct()
    )


def _teacher_scope(request):
    if request.is_teacher_group and not request.is_admin_group:
        teacher = getattr(request.user, 'teacher', None)
        if teacher is None:
            raise PermissionDenied
        return teacher
    return None


# Trang chọn học kỳ + lớp HP
@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def report_index(request):
    semesters    = Semester.objects.all().order_by('-start_date')
    selected_sem = None
    course_classes = CourseClass.objects.none()

    sem_id = request.GET.get('semester')
    page_obj = None
    if sem_id:
        selected_sem   = get_object_or_404(Semester, pk=sem_id)
        course_classes = (
            CourseClass.objects
            .filter(semester=selected_sem)
            .select_related('course', 'teacher__user')
            .order_by('class_code')
        )
        # GV chỉ được xem lớp mình dạy
        teacher = _teacher_scope(request)
        if teacher:
            course_classes = course_classes.filter(teacher=teacher)
        from django.core.paginator import Paginator
        paginator = Paginator(course_classes, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

    return render(request, 'reports/index.html', {
        'semesters'     : semesters,
        'selected_sem'  : selected_sem,
        'course_classes': course_classes,
        'page_obj'      : page_obj,
        'active_menu'   : 'reports',
    })


# Bảng chuyên cần + biểu đồ cột theo buổi
@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def report_class(request, class_id):
    course_class = get_object_or_404(
        CourseClass.objects.select_related('course', 'semester', 'teacher__user'),
        pk=class_id,
    )

    # GV chỉ được xem báo cáo lớp mình dạy
    teacher = _teacher_scope(request)
    if teacher and course_class.teacher_id != teacher.pk:
        raise PermissionDenied

    if request.GET.get('refresh') == '1':
        refresh_class_reports(course_class)

    reports = _get_active_reports(course_class)

    sessions = _build_session_columns(course_class)
    matrix   = _build_matrix(reports, sessions)

    # Thống kê cho stat cards
    total_students = reports.count()
    good_count     = reports.filter(attendance_rate__gte=80).count()
    banned_count   = reports.filter(attendance_rate__lt=80).count()
    warning_count  = reports.filter(absent_rate__gte=20, absent_rate__lt=40).count()
    danger_count   = reports.filter(absent_rate__gte=40).count()
    avg_rate       = 0.0
    if total_students:
        avg_rate = round(sum(r.attendance_rate for r in reports) / total_students, 1)

    # Fetch active enrollments once for chart calculation
    enr_list = Enrollment.objects.filter(
        course_class=course_class,
        is_active=True
    ).values('student_id', 'enrolled_at')
    enrollment_dates = {e['student_id']: e['enrolled_at'].date() for e in enr_list}

    chart_labels  = [f"Buổi {i+1}" for i in range(len(sessions))]
    chart_present = []
    chart_absent  = []
    for s in sessions:
        # Chỉ đếm những sinh viên đã đăng ký trước hoặc trong ngày buổi học diễn ra
        eligible_student_ids = [
            student_id
            for student_id, enr_date in enrollment_dates.items()
            if enr_date <= s.started_at.date()
        ]
        present = AttendanceRecord.objects.filter(
            session=s,
            student_id__in=eligible_student_ids,
            status__in=['present', 'late'],
        ).count()
        absent  = len(eligible_student_ids) - present

        chart_present.append(present)
        chart_absent.append(absent)

    from django.core.paginator import Paginator
    paginator = Paginator(matrix, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/class_report.html', {
        'course_class'  : course_class,
        'reports'       : reports,
        'sessions'      : sessions,
        'page_obj'      : page_obj,
        'total_students': total_students,
        'good_count'    : good_count,
        'banned_count'  : banned_count,
        'warning_count' : warning_count,
        'danger_count'  : danger_count,
        'avg_rate'      : avg_rate,
        'chart_labels'  : chart_labels,
        'chart_present' : chart_present,
        'chart_absent'  : chart_absent,
        'active_menu'   : 'reports',
    })



# Xuất Excel
@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def export_excel(request, class_id):
    """
    Xuất file Excel báo cáo chuyên cần:
    - Hàng đầu: thông tin lớp HP
    - Hàng header: MSSV | Họ Tên | Lớp | Buổi 1 | Buổi 2 | … | Có mặt | Vắng | Trễ | Tỉ lệ %
    - Mỗi hàng SV: status mỗi buổi, tô XANH=có mặt, ĐỎ=vắng, CAM=trễ
    - Hàng cuối: tổng kết toàn lớp
    """
    import openpyxl
    from openpyxl.styles import (Alignment, Border, Font, PatternFill, Side,
                                  numbers)
    from openpyxl.utils import get_column_letter

    course_class = get_object_or_404(
        CourseClass.objects.select_related('course', 'semester', 'teacher__user'),
        pk=class_id,
    )

    # GV chỉ được xuất báo cáo lớp mình dạy
    teacher = _teacher_scope(request)
    if teacher and course_class.teacher_id != teacher.pk:
        raise PermissionDenied

    reports = _get_active_reports(course_class)
    sessions = _build_session_columns(course_class)
    matrix   = _build_matrix(reports, sessions)

    # ---- Màu sắc ----
    GREEN_FILL  = PatternFill('solid', fgColor='C6EFCE')   # có mặt
    RED_FILL    = PatternFill('solid', fgColor='FFC7CE')   # vắng
    ORANGE_FILL = PatternFill('solid', fgColor='FFEB9C')   # trễ
    HEADER_FILL = PatternFill('solid', fgColor='1F4E79')   # header tối
    TITLE_FILL  = PatternFill('solid', fgColor='2E75B6')   # tiêu đề
    TOTAL_FILL  = PatternFill('solid', fgColor='D9E1F2')   # tổng kết
    GOOD_FILL   = PatternFill('solid', fgColor='E2EFDA')   # tỉ lệ tốt
    BAD_FILL    = PatternFill('solid', fgColor='FCE4D6')   # tỉ lệ kém

    WHITE_FONT  = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
    BOLD_FONT   = Font(name='Calibri', bold=True, size=10)
    NORMAL_FONT = Font(name='Calibri', size=10)
    MONO_FONT   = Font(name='Courier New', size=10)

    thin = Side(style='thin', color='BFBFBF')
    BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

    CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
    LEFT   = Alignment(horizontal='left',   vertical='center')

    # ---- Workbook ----
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Báo Cáo Chuyên Cần'

    # Cột cố định: STT | MSSV | Họ Tên | Lớp SH
    FIXED_COLS = 4
    total_cols = FIXED_COLS + len(sessions) + 4

    # ---- Hàng 1: Tiêu đề lớn ----
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    c = ws.cell(1, 1, f'BÁO CÁO CHUYÊN CẦN — {course_class.class_code}')
    c.font      = Font(name='Calibri', bold=True, color='FFFFFF', size=14)
    c.fill      = TITLE_FILL
    c.alignment = CENTER
    ws.row_dimensions[1].height = 28

    # ---- Hàng 2: Thông tin lớp ----
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols)
    teacher_name = course_class.teacher.user.get_full_name() or course_class.teacher.user.username
    info = (
        f"Học phần: {course_class.course.course_name}   |   "
        f"Học kỳ: {course_class.semester}   |   "
        f"Giảng viên: {teacher_name}   |   "
        f"Xuất lúc: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    c = ws.cell(2, 1, info)
    c.font      = Font(name='Calibri', size=10, italic=True)
    c.alignment = CENTER
    ws.row_dimensions[2].height = 18

    # ---- Hàng 3: ngăn cách ----
    ws.row_dimensions[3].height = 6

    # ---- Hàng 4: Header ----
    HEADER_ROW = 4
    headers = ['STT', 'MSSV', 'Họ và Tên', 'Lớp SH']
    for i, s in enumerate(sessions, 1):
        date_str = s.started_at.strftime('%d/%m') if s.started_at else f'B{i}'
        headers.append(f'Buổi {i}\n{date_str}')
    headers += ['Có Mặt', 'Vắng', 'Đi Trễ', 'Tỉ Lệ (%)']

    for col_idx, header in enumerate(headers, 1):
        c = ws.cell(HEADER_ROW, col_idx, header)
        c.font      = WHITE_FONT
        c.fill      = HEADER_FILL
        c.alignment = CENTER
        c.border    = BORDER
    ws.row_dimensions[HEADER_ROW].height = 36

    # ---- Hàng dữ liệu ----
    STATUS_MAP = {
        'present': ('P', GREEN_FILL),
        'late'   : ('T', ORANGE_FILL),
        'absent' : ('V', RED_FILL),
        None     : ('—', None),
    }

    total_present_sum = 0
    total_absent_sum  = 0
    total_late_sum    = 0

    for row_num, row_data in enumerate(matrix, 1):
        rpt    = row_data['report']
        cells  = row_data['cells']
        sv     = rpt.student
        excel_row = HEADER_ROW + row_num

        # STT
        c = ws.cell(excel_row, 1, row_num)
        c.font = NORMAL_FONT; c.alignment = CENTER; c.border = BORDER

        # MSSV
        c = ws.cell(excel_row, 2, sv.student_id)
        c.font = MONO_FONT; c.alignment = CENTER; c.border = BORDER

        # Họ Tên
        c = ws.cell(excel_row, 3, sv.full_name)
        c.font = NORMAL_FONT; c.alignment = LEFT; c.border = BORDER

        # Lớp SH
        c = ws.cell(excel_row, 4, sv.student_class.class_code)
        c.font = NORMAL_FONT; c.alignment = CENTER; c.border = BORDER

        # Từng buổi
        for i, status in enumerate(cells):
            label, fill = STATUS_MAP.get(status, ('—', None))
            c = ws.cell(excel_row, FIXED_COLS + 1 + i, label)
            c.font      = BOLD_FONT
            c.alignment = CENTER
            c.border    = BORDER
            if fill:
                c.fill = fill

        # Tổng kết SV
        c = ws.cell(excel_row, total_cols - 3, rpt.present_count)
        c.font = BOLD_FONT; c.fill = GREEN_FILL; c.alignment = CENTER; c.border = BORDER

        c = ws.cell(excel_row, total_cols - 2, rpt.absent_count)
        c.font = BOLD_FONT; c.fill = RED_FILL; c.alignment = CENTER; c.border = BORDER

        c = ws.cell(excel_row, total_cols - 1, rpt.late_count)
        c.font = BOLD_FONT; c.fill = ORANGE_FILL; c.alignment = CENTER; c.border = BORDER

        rate = rpt.attendance_rate
        c = ws.cell(excel_row, total_cols, f'{rate:.1f}%')
        c.font      = BOLD_FONT
        c.fill      = GOOD_FILL if rate >= 80 else BAD_FILL
        c.alignment = CENTER
        c.border    = BORDER

        total_present_sum += rpt.present_count
        total_absent_sum  += rpt.absent_count
        total_late_sum    += rpt.late_count

        # Xen kẽ màu
        if row_num % 2 == 0:
            for col in range(1, total_cols + 1):
                cell = ws.cell(excel_row, col)
                if not cell.fill or cell.fill.fgColor.rgb in ('00000000', 'FFFFFFFF'):
                    cell.fill = PatternFill('solid', fgColor='F8FAFF')

    # ---- Hàng tổng kết ----
    total_row = HEADER_ROW + len(matrix) + 1
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=FIXED_COLS)
    c = ws.cell(total_row, 1, f'TỔNG KẾT  ({len(matrix)} sinh viên)')
    c.font = Font(name='Calibri', bold=True, size=11, color='1F4E79')
    c.fill = TOTAL_FILL; c.alignment = CENTER; c.border = BORDER

    # Ô trống ở các cột buổi
    for i in range(len(sessions)):
        c = ws.cell(total_row, FIXED_COLS + 1 + i)
        c.fill = TOTAL_FILL; c.border = BORDER

    # Tổng
    for val, col_offset in [(total_present_sum, -3), (total_absent_sum, -2), (total_late_sum, -1)]:
        c = ws.cell(total_row, total_cols + col_offset, val)
        c.font = Font(name='Calibri', bold=True, size=11)
        c.fill = TOTAL_FILL; c.alignment = CENTER; c.border = BORDER

    # Tỉ lệ TB
    avg = 0.0
    if len(matrix):
        avg = sum(r['report'].attendance_rate for r in matrix) / len(matrix)
    c = ws.cell(total_row, total_cols, f'{avg:.1f}%')
    c.font      = Font(name='Calibri', bold=True, size=11,
                       color='375623' if avg >= 80 else '9C0006')
    c.fill      = TOTAL_FILL
    c.alignment = CENTER
    c.border    = BORDER
    ws.row_dimensions[total_row].height = 24

    # Chú thích
    note_row = total_row + 2
    ws.cell(note_row, 1, 'Chú thích:').font = BOLD_FONT
    legends = [
        (note_row, 2, 'P = Có mặt', GREEN_FILL),
        (note_row, 3, 'V = Vắng',   RED_FILL),
        (note_row, 4, 'T = Đi trễ', ORANGE_FILL),
        (note_row, 5, '— = Chưa có dữ liệu', None),
    ]
    for r, col, text, fill in legends:
        c = ws.cell(r, col, text)
        c.font = NORMAL_FONT
        if fill:
            c.fill = fill

    # Độ rộng cột
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 13
    ws.column_dimensions['C'].width = 24
    ws.column_dimensions['D'].width = 12
    for i in range(len(sessions)):
        ws.column_dimensions[get_column_letter(FIXED_COLS + 1 + i)].width = 8
    ws.column_dimensions[get_column_letter(total_cols - 3)].width = 10
    ws.column_dimensions[get_column_letter(total_cols - 2)].width = 8
    ws.column_dimensions[get_column_letter(total_cols - 1)].width = 8
    ws.column_dimensions[get_column_letter(total_cols)].width     = 11

    # Đóng băng hàng header
    ws.freeze_panes = ws.cell(HEADER_ROW + 1, FIXED_COLS + 1)

    filename = f"chuyen_can_{course_class.class_code}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



# Lịch sử điểm danh từng SV
@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def student_attendance(request, student_id):
    """
    Trang chi tiết lịch sử điểm danh của 1 sinh viên.
    Lọc theo lớp HP nếu có ?class=<id>.
    """
    student = get_object_or_404(Student.objects.select_related('student_class'), pk=student_id)
    teacher = _teacher_scope(request)

    # Lấy tất cả lớp HP SV đã đăng ký
    enrollments = (
        Enrollment.objects
        .filter(student=student)
        .select_related('course_class__course', 'course_class__semester')
        .order_by('-course_class__semester__start_date')
    )

    # GV chỉ được xem SV trong lớp mình dạy
    if teacher:
        enrollments = enrollments.filter(course_class__teacher=teacher)
        if not enrollments.filter(is_active=True).exists():
            raise PermissionDenied

    selected_class = None
    class_id = request.GET.get('class')
    if class_id:
        course_class_qs = CourseClass.objects.all()
        if teacher:
            course_class_qs = course_class_qs.filter(teacher=teacher)
        selected_class = get_object_or_404(course_class_qs, pk=class_id)

    # Lấy các session của lớp SV có đăng ký
    sessions_qs = (
        AttendanceSession.objects
        .filter(course_class__enrollments__student=student, course_class__enrollments__is_active=True)
        .select_related('course_class__course', 'course_class__semester')
        .order_by('-started_at')
    )
    if teacher:
        sessions_qs = sessions_qs.filter(course_class__teacher=teacher)
    if selected_class:
        sessions_qs = sessions_qs.filter(course_class=selected_class)
        
    records = AttendanceRecord.objects.filter(student=student, session__in=sessions_qs)
    record_map = {r.session_id: r for r in records}

    history = []
    for s in sessions_qs:
        rec = record_map.get(s.id)
        if rec:
            status, method, conf, note = rec.status, rec.method, rec.confidence, rec.note
            rec_id = rec.pk
        else:
            status = 'absent' if s.status == 'closed' else 'pending'
            method, conf, note = '', 0.0, ''
            rec_id = None
            
        history.append({
            'session': s,
            'status': status,
            'method': method,
            'confidence': conf,
            'note': note,
            'rec_id': rec_id
        })

    from django.core.paginator import Paginator
    history_paginator = Paginator(history, 10)
    history_page_obj = history_paginator.get_page(request.GET.get('page', 1))

    # Tổng hợp theo lớp HP
    reports = (
        AttendanceReport.objects
        .filter(student=student)
        .select_related('course_class__course', 'course_class__semester')
        .order_by('-course_class__semester__start_date')
    )
    if teacher:
        reports = reports.filter(course_class__teacher=teacher)
    if selected_class:
        reports = reports.filter(course_class=selected_class)

    return render(request, 'reports/student_attendance.html', {
        'student'       : student,
        'enrollments'   : enrollments,
        'selected_class': selected_class,
        'history'       : history,
        'history_page_obj': history_page_obj,
        'reports'       : reports,
        'active_menu'   : 'reports',
    })


# Sửa thủ công 1 AttendanceRecord
@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
@require_http_methods(['POST'])
def attendance_edit(request, session_id, student_id):
    """
    Cho phép GV sửa trạng thái điểm danh khi nhận diện sai.
    POST: status (present|absent|late), note
    Sau khi sửa → refresh báo cáo + kiểm tra cảnh báo.
    """
    from reports.services import refresh_report
    from notifications.services import check_and_notify

    session = get_object_or_404(
        AttendanceSession.objects.select_related('course_class__teacher'),
        pk=session_id,
    )
    student = get_object_or_404(Student, pk=student_id)
    teacher = _teacher_scope(request)

    if teacher and session.course_class.teacher_id != teacher.pk:
        raise PermissionDenied
    if not Enrollment.objects.filter(
        course_class=session.course_class,
        student=student,
        is_active=True,
    ).exists():
        raise PermissionDenied

    new_status = request.POST.get('status')
    if new_status not in ('present', 'absent', 'late'):
        messages.error(request, 'Trạng thái không hợp lệ.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    record, created = AttendanceRecord.objects.get_or_create(
        session=session,
        student=student,
        defaults={
            'status': new_status,
            'method': 'manual',
            'note': request.POST.get('note', '').strip()[:200]
        }
    )

    if not created:
        record.status = new_status
        record.method = 'manual'
        record.note   = request.POST.get('note', '').strip()[:200]
        record.save(update_fields=['status', 'method', 'note'])

    # Cập nhật báo cáo + kiểm tra cảnh báo
    report = refresh_report(student, session.course_class)
    check_and_notify(student, session.course_class, report)

    messages.success(
        request,
        f'Đã cập nhật điểm danh {student.full_name} → '
        f'{dict([("present","Có mặt"), ("late","Đi trễ"), ("absent","Vắng")]).get(new_status)}'
    )

    # Quay lại trang chi tiết SV, đúng lớp HP
    return redirect(
        f'/reports/student/{student.pk}/?class={session.course_class.pk}'
    )
