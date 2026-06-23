import json
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Count, Avg, Q, FloatField
from django.db.models.functions import Cast

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required, module_permission_required

from students.models import Student
from courses.models import CourseClass
from academics.models import Semester
from attendance.models import AttendanceSession, AttendanceRecord
from reports.models import AttendanceReport


def home(request):
    """Trang chủ giới thiệu hệ thống EduFace (public)."""
    return render(request, 'dashboards/home.html')


@login_required
def dashboard(request):
    """Dashboard chính."""
    user = request.user

    # Sinh viên → chuyển về trang hồ sơ sinh viên
    if hasattr(user, 'student') and user.student is not None:
        return redirect('students:student_profile')

    # Nếu không phải sinh viên, kiểm tra quyền xem dashboard
    if not (user.is_superuser or getattr(request, 'is_admin_group', False) or getattr(request, 'can_view_dashboard', False) or getattr(request, 'user_permissions', {}).get('dashboard', {}).get('view', False)):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Nếu là Giảng viên, có thể lọc bớt dữ liệu (ví dụ chỉ lấy các lớp của GV đó)
    # Tuy nhiên, đối với "Tổng Quan" cấp trường, thường Admin thấy tất cả, GV cũng có thể thấy tổng quan
    # hoặc chỉ thấy của mình. Ở đây ta ưu tiên tính trên toàn trường (Admin view).
    # Nếu cần thu hẹp cho GV, ta lọc theo `teacher = user.teacher`.

    
    is_admin = request.is_admin_group
    teacher = getattr(user, 'teacher', None) if not is_admin else None

    semesters = Semester.objects.all().order_by('-start_date')
    sem_id = request.GET.get('semester')
    if sem_id:
        active_semester = Semester.objects.filter(pk=sem_id).first()
    else:
        active_semester = Semester.objects.filter(is_active=True).first()
    
    # 1. Thống kê tổng quan
    total_students = Student.objects.filter(is_active=True).count()
    
    course_classes_qs = CourseClass.objects.filter(semester=active_semester)
    if teacher:
        course_classes_qs = course_classes_qs.filter(teacher=teacher)
    total_classes = course_classes_qs.count()

    today = timezone.localdate()
    today_sessions_qs = AttendanceSession.objects.filter(started_at__date=today)
    if teacher:
        today_sessions_qs = today_sessions_qs.filter(course_class__teacher=teacher)
    today_sessions = today_sessions_qs.count()
    completed_sessions = today_sessions_qs.filter(status='closed').count()

    reports_qs = AttendanceReport.objects.filter(course_class__semester=active_semester)
    if teacher:
        reports_qs = reports_qs.filter(course_class__teacher=teacher)
    
    avg_attendance = reports_qs.aggregate(avg=Avg('attendance_rate'))['avg'] or 0.0

    # 2. Thống kê xu hướng điểm danh (7 ngày qua)
    past_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    trend_labels = [d.strftime('%d/%m') for d in past_7_days]
    trend_present = []
    trend_absent = []

    for d in past_7_days:
        records_qs = AttendanceRecord.objects.filter(session__started_at__date=d)
        if teacher:
            records_qs = records_qs.filter(session__course_class__teacher=teacher)
            
        stats = records_qs.aggregate(
            present=Count('id', filter=Q(status='present') | Q(status='late')),
            absent=Count('id', filter=Q(status='absent')),
        )
        trend_present.append(stats['present'])
        trend_absent.append(stats['absent'])

    # 3. Thống kê theo Khoa/Ngành (Bar Chart)
    # Group theo department của student_class
    dept_stats = reports_qs.values('student__student_class__department__name') \
                           .annotate(avg_rate=Avg('attendance_rate')) \
                           .order_by('-avg_rate')
    
    dept_labels = []
    dept_rates = []
    for d in dept_stats:
        dept_name = d['student__student_class__department__name'] or 'Khác'
        dept_labels.append(dept_name)
        dept_rates.append(round(d['avg_rate'], 1))

    # 4. Top 5 lớp học phần
    # Lấy trung bình attendance_rate nhóm theo lớp học phần
    class_stats = reports_qs.values('course_class__id', 'course_class__class_code', 'course_class__course__course_name') \
                            .annotate(avg_rate=Avg('attendance_rate'))
                            
    class_stats_list = list(class_stats)
    class_stats_list.sort(key=lambda x: x['avg_rate'], reverse=True)
    
    top_best = class_stats_list[:5]
    top_worst = class_stats_list[-5:]
    top_worst.reverse() # Xếp từ thấp lên cao

    context = {
        'active_menu': 'dashboard',
        'active_semester': active_semester,
        'semesters': semesters,
        'total_students': total_students,
        'total_classes': total_classes,
        'today_sessions': today_sessions,
        'completed_sessions': completed_sessions,
        'avg_attendance': round(avg_attendance, 1),
        
        'trend_labels': json.dumps(trend_labels),
        'trend_present': json.dumps(trend_present),
        'trend_absent': json.dumps(trend_absent),
        
        'dept_labels': json.dumps(dept_labels),
        'dept_rates': json.dumps(dept_rates),
        
        'top_best': top_best,
        'top_worst': top_worst,
    }
    return render(request, 'dashboards/dashboard.html', context)
