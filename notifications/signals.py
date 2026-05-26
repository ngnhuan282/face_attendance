# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from attendance.models import AttendanceRecord, AttendanceSession
from reports.services import refresh_report
from notifications.services import check_and_notify, check_class_after_session

@receiver(post_save, sender=AttendanceRecord)
def trigger_notification_on_record_save(sender, instance, **kwargs):
    session = instance.session
    
    # Chỉ xử lý khi buổi điểm danh này đã ở trạng thái ĐÃ ĐÓNG
    if session.status == 'closed':
        student = instance.student
        course_class = session.course_class
        
        # làm mới bảng báo cáo chuyên cần cho sinh viên này
        report = refresh_report(student, course_class)
        
        # kiểm tra ngưỡng vắng và sinh/xóa cảnh báo tương ứng
        check_and_notify(student, course_class, report)
        
@receiver(post_save, sender=AttendanceSession)
def trigger_notifications_on_session_close(sender, instance, **kwargs):
    if instance.status == 'closed':
        check_class_after_session(instance)