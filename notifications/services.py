from __future__ import annotations

from courses.models import CourseClass
from students.models import Student

from .models import Notification

ABSENT_WARNING_THRESHOLD = 20.0
ABSENT_DANGER_THRESHOLD  = 40.0


def check_and_notify(
    student: Student,
    course_class: CourseClass,
    report, 
) -> Notification | None:
    absent_pct = report.absent_rate

    if absent_pct >= ABSENT_DANGER_THRESHOLD:
        noti_type = 'absent_danger'
    elif absent_pct >= ABSENT_WARNING_THRESHOLD:
        noti_type = 'absent_warning'
    else:
        Notification.objects.filter(
            student=student,
            course_class=course_class,
        ).delete()
        return None

    noti, created = Notification.objects.update_or_create(
        student=student,
        course_class=course_class,
        defaults={
            'noti_type'      : noti_type,
            'absent_count'   : report.absent_count,
            'total_sessions' : report.total_sessions,
            'absent_percent' : absent_pct,
            'is_read'        : False,
        },
    )
    return noti



# Gọi sau khi đóng 1 buổi điểm danh
def check_class_after_session(session) -> list[Notification]:
    from reports.services import refresh_report
    from courses.models import Enrollment
    enrollments = Enrollment.objects.filter(
        course_class=session.course_class,
        is_active=True
    ).select_related('student')
    
    notis = []
    for enrollment in enrollments:
        report = refresh_report(enrollment.student, session.course_class)
        
        noti = check_and_notify(enrollment.student, session.course_class, report)
        if noti:
            notis.append(noti)
    return notis