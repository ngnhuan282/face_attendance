from django.db import models
from students.models import Student
from courses.models import CourseClass

class Notification(models.Model):
    TYPE_CHOICES = [
        ('absent_warning', 'Cảnh báo vắng (> 20%)'),
        ('absent_danger', 'Nguy hiểm vắng (> 40%)'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Sinh viên'
    )
    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Lớp học phần'
    )
    noti_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Loại cảnh báo'
    )
    absent_count = models.IntegerField(verbose_name='Số buổi vắng')
    total_sessions = models.IntegerField(verbose_name='Tổng số buổi đã học')
    absent_percent = models.FloatField(verbose_name='Tỉ lệ vắng (%)')
    is_read = models.BooleanField(default=False, verbose_name='Đã đọc')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm tạo')

    class Meta:
        verbose_name = 'Cảnh báo vắng mặt'
        verbose_name_plural = 'Cảnh báo vắng mặt'
        ordering = ['-created_at']
        unique_together = [('student', 'course_class')]

    def __str__(self):
        return (
            f"[{self.get_noti_type_display()}] "
            f"{self.student.full_name} — "
            f"{self.course_class.class_code} — "
            f"{self.absent_percent:.1f}%"
        )