from __future__ import annotations

from typing import TYPE_CHECKING

from attendance.models import AttendanceRecord, AttendanceSession
from courses.models import CourseClass
from students.models import Student

from .models import AttendanceReport

if TYPE_CHECKING:
    pass



ABSENT_WARNING_THRESHOLD = 20.0
ABSENT_DANGER_THRESHOLD  = 40.0



#tính tỉ lệ chuyên cần
def compute_attendance_rate(
    student: Student,
    course_class: CourseClass,
) -> dict:
    from courses.models import Enrollment

    enrollment = Enrollment.objects.filter(student=student, course_class=course_class).first()

    if enrollment:
        closed_sessions = AttendanceSession.objects.filter(
            course_class=course_class,
            status='closed',
            started_at__date__gte=enrollment.enrolled_at.date()
        )
    else:
        closed_sessions = AttendanceSession.objects.filter(
            course_class=course_class,
            status='closed',
        )
    total_sessions = closed_sessions.count()

    if total_sessions == 0:
        return {
            "total_sessions" : 0,
            "present_count"  : 0,
            "absent_count"   : 0,
            "late_count"     : 0,
            "attendance_rate": 0.0,
            "absent_rate"    : 0.0,
        }

    # Lấy bản ghi điểm danh của sinh viên này trong các session trên
    records = AttendanceRecord.objects.filter(
        session__in=closed_sessions,
        student=student,
    )

    present_count = records.filter(status='present').count()
    late_count    = records.filter(status='late').count()
    absent_count  = total_sessions - present_count - late_count

    #có mặt = present + late (đi trễ vẫn tính)
    effective_present = present_count + late_count
    attendance_rate   = round(effective_present / total_sessions * 100, 2)
    absent_rate       = round(absent_count / total_sessions * 100, 2)

    return {
        "total_sessions" : total_sessions,
        "present_count"  : present_count,
        "absent_count"   : absent_count,
        "late_count"     : late_count,
        "attendance_rate": attendance_rate,
        "absent_rate"    : absent_rate,
    }


# Upsert báo cáo cho 1 sinh viên / 1 lớp HP

def refresh_report(
    student: Student,
    course_class: CourseClass,
) -> AttendanceReport:
    stats = compute_attendance_rate(student, course_class)

    report, _ = AttendanceReport.objects.update_or_create(
        student=student,
        course_class=course_class,
        defaults={
            "total_sessions" : stats["total_sessions"],
            "present_count"  : stats["present_count"],
            "absent_count"   : stats["absent_count"],
            "late_count"     : stats["late_count"],
            "attendance_rate": stats["attendance_rate"],
            "absent_rate"    : stats["absent_rate"],
        },
    )
    return report


# Làm mới toàn bộ báo cáo của 1 lớp HP

def refresh_class_reports(course_class: CourseClass) -> list[AttendanceReport]:
    from courses.models import Enrollment

    enrollments = Enrollment.objects.filter(
        course_class=course_class,
        is_active=True,
    ).select_related('student')

    reports = []
    for enrollment in enrollments:
        report = refresh_report(enrollment.student, course_class)
        reports.append(report)

    return reports


# Làm mới báo cáo ngay sau khi 1 buổi điểm danh kết thúc

def refresh_session_reports(session: AttendanceSession) -> list[AttendanceReport]:
    from notifications.services import check_and_notify

    records = session.records.select_related('student').all()
    reports = []

    for record in records:
        report = refresh_report(record.student, session.course_class)
        reports.append(report)
        # Kiểm tra và tạo cảnh báo nếu vắng vượt ngưỡng
        check_and_notify(record.student, session.course_class, report)

    return reports
