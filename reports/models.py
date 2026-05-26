from django.db import models
from students.models import Student
from courses.models import CourseClass
from academics.models import Semester


class AttendanceReport(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_reports',
        verbose_name='Sinh viên'
    )
    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.CASCADE,
        related_name='attendance_reports',
        verbose_name='Lớp học phần'
    )
    total_sessions = models.IntegerField(
        default=0,
        verbose_name='Tổng buổi đã học'
    )
    present_count = models.IntegerField(
        default=0,
        verbose_name='Số buổi có mặt'
    )
    absent_count = models.IntegerField(
        default=0,
        verbose_name='Số buổi vắng'
    )
    late_count = models.IntegerField(
        default=0,
        verbose_name='Số buổi đi trễ'
    )
    attendance_rate = models.FloatField(
        default=0.0,
        verbose_name='Tỉ lệ có mặt (%)'
    )
    absent_rate = models.FloatField(
        default=0.0,
        verbose_name='Tỉ lệ vắng (%)'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Cập nhật lúc'
    )

    class Meta:
        verbose_name = 'Báo cáo chuyên cần'
        verbose_name_plural = 'Báo cáo chuyên cần'
        unique_together = [('student', 'course_class')]
        ordering = ['course_class', 'student']

    def __str__(self):
        return (
            f"{self.student.student_id} — "
            f"{self.course_class.class_code} — "
            f"{self.attendance_rate:.1f}%"
        )
