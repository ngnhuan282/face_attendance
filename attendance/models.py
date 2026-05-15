from django.db import models
from django.contrib.auth.models import User
from courses.models import CourseClass
from schedules.models import Schedule
from students.models import Student

class AttendanceSession(models.Model):
    """Buổi điểm danh — do giảng viên tạo, gắn với 1 buổi lịch học"""
    STATUS_CHOICES = [
        ('open', 'Đang mở'),
        ('closed', 'Đã đóng'),
    ]

    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        verbose_name='Lớp học phần'
    )
    schedule = models.OneToOneField(
        Schedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_session',
        verbose_name='Buổi lịch học'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_sessions',
        verbose_name='Giảng viên tạo'
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Bắt đầu lúc')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='Kết thúc lúc')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name='Trạng thái'
    )
    note = models.TextField(blank=True, verbose_name='Ghi chú')

    class Meta:
        verbose_name = 'Buổi điểm danh'
        verbose_name_plural = 'Buổi điểm danh'
        ordering = ['-started_at']

    def __str__(self):
        return (
            f"{self.course_class.class_code} — "
            f"{self.started_at.strftime('%d/%m/%Y %H:%M')}"
        )

class AttendanceRecord(models.Model):
    """Bản ghi điểm danh của từng sinh viên trong 1 buổi"""
    STATUS_CHOICES = [
        ('present', 'Có mặt'),
        ('absent', 'Vắng'),
        ('late', 'Đi trễ'),
    ]

    METHOD_CHOICES = [
        ('face', 'Nhận diện khuôn mặt'),
        ('manual', 'Thủ công'),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='Buổi điểm danh'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name='Sinh viên'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='absent',
        verbose_name='Trạng thái'
    )
    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        default='face',
        verbose_name='Phương thức'
    )
    confidence = models.FloatField(default=0.0, verbose_name='Độ chính xác')
    timestamp = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm nhận diện')
    note = models.CharField(max_length=200, blank=True, verbose_name='Ghi chú')

    class Meta:
        verbose_name = 'Bản ghi điểm danh'
        verbose_name_plural = 'Bản ghi điểm danh'
        unique_together = [('session', 'student')]
        ordering = ['session', 'student']

    def __str__(self):
        return (
            f"{self.student.student_id} — "
            f"{self.get_status_display()} — "
            f"{self.session}"
        )