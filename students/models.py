from django.db import models
from academics.models import Department

class StudentClass(models.Model):
    """Lớp sinh hoạt (VD: DHKTPM17A)"""
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='student_classes',
        verbose_name='Ngành'
    )
    class_code = models.CharField(max_length=20, unique=True, verbose_name='Mã lớp')
    class_name = models.CharField(max_length=50, verbose_name='Tên lớp')
    intake_year = models.IntegerField(verbose_name='Năm nhập học')

    class Meta:
        verbose_name = 'Lớp sinh hoạt'
        verbose_name_plural = 'Lớp sinh hoạt'
        ordering = ['-intake_year', 'class_code']

    def __str__(self):
        return f"{self.class_code} — {self.class_name}"

class Student(models.Model):
    """Sinh viên"""
    student_class = models.ForeignKey(
        StudentClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Lớp sinh hoạt'
    )
    student_id = models.CharField(max_length=20, unique=True, verbose_name='MSSV')
    full_name = models.CharField(max_length=100, verbose_name='Họ tên')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Ngày sinh')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=15, blank=True, verbose_name='Số điện thoại')
    photo = models.ImageField(
        upload_to='student_photos/',
        null=True,
        blank=True,
        verbose_name='Ảnh khuôn mặt'
    )
    is_active = models.BooleanField(default=True, verbose_name='Đang học')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        verbose_name = 'Sinh viên'
        verbose_name_plural = 'Sinh viên'
        ordering = ['student_class', 'full_name']

    def __str__(self):
        return f"{self.student_id} — {self.full_name}"