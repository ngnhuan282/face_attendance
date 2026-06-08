from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from recognition.encoding_tasks import enqueue_student_encoding_update

from .models import Student


TRACKED_FIELDS = {"photo", "student_id", "full_name", "is_active"}


@receiver(pre_save, sender=Student)
def remember_previous_student_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_face_state = None
        return

    previous = sender.objects.filter(pk=instance.pk).only(
        "photo",
        "student_id",
        "full_name",
        "is_active",
    ).first()

    if not previous:
        instance._previous_face_state = None
        return

    instance._previous_face_state = {
        "photo": previous.photo.name if previous.photo else "",
        "student_id": previous.student_id,
        "full_name": previous.full_name,
        "is_active": previous.is_active,
    }


@receiver(post_save, sender=Student)
def rebuild_face_encodings(sender, instance, created, raw=False, update_fields=None, **kwargs):
    if raw:
        return

    if update_fields is not None and TRACKED_FIELDS.isdisjoint(update_fields):
        return

    current_state = {
        "photo": instance.photo.name if instance.photo else "",
        "student_id": instance.student_id,
        "full_name": instance.full_name,
        "is_active": instance.is_active,
    }
    previous_state = getattr(instance, "_previous_face_state", None)
    face_data_changed = created or current_state != previous_state

    if created and not current_state["photo"]:
        return

    if not face_data_changed:
        return

    previous_student_id = previous_state["student_id"] if previous_state else None

    transaction.on_commit(
        lambda: enqueue_student_encoding_update(instance.pk, previous_student_id)
    )


@receiver(post_delete, sender=Student)
def remove_deleted_student_encoding(sender, instance, **kwargs):
    transaction.on_commit(
        lambda: enqueue_student_encoding_update(instance.pk, instance.student_id)
    )
