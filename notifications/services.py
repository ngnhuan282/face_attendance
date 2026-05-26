from __future__ import annotations

from courses.models import CourseClass
from students.models import Student

from .models import Notification

# Ngưỡng cảnh báo
ABSENT_WARNING_THRESHOLD = 20.0
ABSENT_DANGER_THRESHOLD  = 40.0


# Hàm kiểm tra & tạo Notification cho 1 SV / 1 lớp HP
def check_and_notify(
    student: Student,
    course_class: CourseClass,
    report, 
) -> Notification | None:
    absent_pct = report.absent_rate

    # Xác định loại cảnh báo
    if absent_pct >= ABSENT_DANGER_THRESHOLD:
        noti_type = 'absent_danger'
    elif absent_pct >= ABSENT_WARNING_THRESHOLD:
        noti_type = 'absent_warning'
    else:
        # Không vượt ngưỡng — xóa cảnh báo cũ nếu có
        Notification.objects.filter(
            student=student,
            course_class=course_class,
        ).delete()
        return None

    # Upsert: 1 SV chỉ có tối đa 1 cảnh báo mới nhất per lớp HP
    noti, created = Notification.objects.update_or_create(
        student=student,
        course_class=course_class,
        defaults={
            'noti_type'      : noti_type,
            'absent_count'   : report.absent_count,
            'total_sessions' : report.total_sessions,
            'absent_percent' : absent_pct,
            'is_read'        : False,   # đặt lại thành chưa đọc khi có thay đổi
        },
    )
    return noti



# Gọi sau khi đóng 1 buổi điểm danh

def check_class_after_session(session) -> list[Notification]:
    from reports.services import refresh_report

    records = session.records.select_related('student').all()
    notis   = []

    for record in records:
        report = refresh_report(record.student, session.course_class)
        noti   = check_and_notify(record.student, session.course_class, report)
        if noti:
            notis.append(noti)

    return notis
