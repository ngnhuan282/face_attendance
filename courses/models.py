from django.db import models
from academics.models import Department, Semester
from schedules.models import Room
from accounts.models import Teacher

class Course(models.Model):
    """Học phần / Môn học"""
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='Ngành'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Phòng học'
    )
    course_code = models.CharField(max_length=20, unique=True, verbose_name='Mã học phần')
    course_name = models.CharField(max_length=200, verbose_name='Tên học phần')
    credits = models.IntegerField(default=3, verbose_name='Số tín chỉ')
    description = models.TextField(blank=True, verbose_name='Mô tả')

    class Meta:
        verbose_name = 'Học phần'
        verbose_name_plural = 'Học phần'
        ordering = ['course_code']

    def __str__(self):
        return f"{self.course_code} — {self.course_name}"

class CourseClass(models.Model):
    """Lớp học phần (1 học phần có thể mở nhiều lớp / học kỳ)"""
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='course_classes',
        verbose_name='Học phần'
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name='course_classes',
        verbose_name='Học kỳ'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='course_classes',
        verbose_name='Giảng viên'
    )
    class_code = models.CharField(max_length=30, verbose_name='Mã lớp HP')
    max_students = models.IntegerField(default=40, verbose_name='Sĩ số tối đa')
    total_sessions = models.IntegerField(default=15, verbose_name='Tổng số buổi')

    class Meta:
        verbose_name = 'Lớp học phần'
        verbose_name_plural = 'Lớp học phần'
        unique_together = [('course', 'semester', 'class_code')]
        ordering = ['semester', 'class_code']

    def __str__(self):
        return f"{self.class_code} — {self.course.course_name} ({self.semester})"

class Enrollment(models.Model):
    """Đăng ký học phần của sinh viên"""

    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Lớp học phần'
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Sinh viên'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày đăng ký')
    is_active = models.BooleanField(default=True, verbose_name='Còn học')

    class Meta:
        verbose_name = 'Đăng ký học phần'
        verbose_name_plural = 'Đăng ký học phần'
        unique_together = [('course_class', 'student')]
        ordering = ['course_class', 'student']

    def __str__(self):
        return f"{self.student} → {self.course_class}"