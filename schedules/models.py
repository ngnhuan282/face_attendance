from django.db import models
from courses.models import CourseClass

class Room(models.Model):
    """Phòng học"""
    room_code = models.CharField(max_length=20, unique=True, verbose_name='Mã phòng')
    building = models.CharField(max_length=50, blank=True, verbose_name='Tòa nhà')
    capacity = models.IntegerField(default=40, verbose_name='Sức chứa')
    has_camera = models.BooleanField(default=False, verbose_name='Có camera điểm danh')

    class Meta:
        verbose_name = 'Phòng học'
        verbose_name_plural = 'Phòng học'
        ordering = ['building', 'room_code']

    def __str__(self):
        prefix = f"{self.building} — " if self.building else ""
        return f"{prefix}{self.room_code}"

class Schedule(models.Model):
    """Lịch học từng buổi của một lớp học phần"""
    DAY_CHOICES = [
        (2, 'Thứ Hai'), (3, 'Thứ Ba'), (4, 'Thứ Tư'), (5, 'Thứ Năm'),
        (6, 'Thứ Sáu'), (7, 'Thứ Bảy'), (8, 'Chủ Nhật'),
    ]

    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Lớp học phần'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedules',
        verbose_name='Phòng học'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES, verbose_name='Thứ trong tuần')
    start_period = models.IntegerField(verbose_name='Tiết bắt đầu')   
    end_period = models.IntegerField(verbose_name='Tiết kết thúc')     
    date = models.DateField(verbose_name='Ngày học')
    session_number = models.IntegerField(verbose_name='Buổi thứ')

    class Meta:
        verbose_name = 'Lịch học'
        verbose_name_plural = 'Lịch học'
        unique_together = [('course_class', 'date')]
        ordering = ['date', 'start_period']

    def __str__(self):
        return (
            f"{self.course_class.class_code} — "
            f"Buổi {self.session_number} — {self.date}"
        )