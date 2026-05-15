from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME


@receiver(post_migrate)
def ensure_default_groups(sender, **kwargs):
    """Create default auth groups after migrations.

    Week 1 plan: Admin / GiangVien groups exist for permission checks.
    """
    Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
    Group.objects.get_or_create(name=TEACHER_GROUP_NAME)
