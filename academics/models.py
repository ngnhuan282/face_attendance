from django.db import models

class Faculty(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name='Mã khoa')
    name = models.CharField(max_length=100, verbose_name='Tên khoa')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Khoa'
        verbose_name_plural = 'Khoa'
        ordering = ['code']

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments', verbose_name='Khoa')
    code = models.CharField(max_length=10, unique=True, verbose_name='Mã ngành')
    name = models.CharField(max_length=100, verbose_name='Tên ngành')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ngành'
        verbose_name_plural = 'Ngành'
        ordering = ['code']

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name='Năm học')
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    end_date = models.DateField(verbose_name='Ngày kết thúc')
    is_active = models.BooleanField(default=False, verbose_name='Đang hoạt động')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Năm học'
        verbose_name_plural = 'Năm học'
        ordering = ['-start_date']

    def __str__(self) -> str:
        return self.name

class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters', verbose_name='Năm học')
    semester_num = models.IntegerField(verbose_name='Học kỳ')
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    end_date = models.DateField(verbose_name='Ngày kết thúc')
    is_active = models.BooleanField(default=False, verbose_name='Đang hoạt động')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Học kỳ'
        verbose_name_plural = 'Học kỳ'
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'semester_num'],
                name='uniq_semester_per_academic_year',
            )
        ]
        ordering = ['-academic_year__start_date', 'semester_num']

    def __str__(self) -> str:
        return f"{self.academic_year} - HK{self.semester_num}"