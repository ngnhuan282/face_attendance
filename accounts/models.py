from django.db import models
from django.contrib.auth.models import User
from academics.models import Department

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)