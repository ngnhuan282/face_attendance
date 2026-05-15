from django.db import models
from django.contrib.auth.models import User
from academics.models import Department

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='teachers/avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Giảng viên'
        verbose_name_plural = 'Giảng viên'
        ordering = ['teacher_id']

    def __str__(self) -> str:
        full_name = self.user.get_full_name() or self.user.username
        return f"{self.teacher_id} - {full_name}"