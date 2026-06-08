import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from django.db import close_old_connections

from .face_encoder import encode_student_photo
from .utils import ENCODINGS_FILE, create_empty_encodings, load_encodings, save_encodings


logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="face-encoding")
_encodings_lock = Lock()


def _load_existing_encodings():
    try:
        return load_encodings(require_data=False)
    except FileNotFoundError:
        return create_empty_encodings()


def _remove_student_vectors(data, student_ids):
    student_ids = {student_id for student_id in student_ids if student_id}
    if not student_ids:
        return data

    filtered = create_empty_encodings()
    for encoding, student_id, name in zip(
        data.get("encodings", []),
        data.get("student_ids", []),
        data.get("names", []),
    ):
        if student_id in student_ids:
            continue
        filtered["encodings"].append(encoding)
        filtered["student_ids"].append(student_id)
        filtered["names"].append(name)

    return filtered


def update_student_encoding(student_pk, previous_student_id=None):
    close_old_connections()
    try:
        from students.models import Student

        student = Student.objects.filter(pk=student_pk).first()
        student_ids_to_remove = {previous_student_id}
        if student:
            student_ids_to_remove.add(student.student_id)

        with _encodings_lock:
            data = _remove_student_vectors(_load_existing_encodings(), student_ids_to_remove)

            if student and student.is_active and student.photo:
                encoding = encode_student_photo(student)
                if encoding is not None:
                    data["encodings"].append(encoding)
                    data["student_ids"].append(student.student_id)
                    data["names"].append(student.full_name)

            save_encodings(data, ENCODINGS_FILE)
    except Exception:
        logger.exception("Khong the cap nhat vector nhan dien cho sinh vien pk=%s.", student_pk)
    finally:
        close_old_connections()


def enqueue_student_encoding_update(student_pk, previous_student_id=None):
    return _executor.submit(update_student_encoding, student_pk, previous_student_id)
