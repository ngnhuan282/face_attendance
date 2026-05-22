import os
import sys
from pathlib import Path
from PIL import Image

import face_recognition
import numpy as np
from django.apps import apps

try:
    from .utils import ENCODINGS_FILE, create_empty_encodings, save_encodings
except ImportError:
    from utils import ENCODINGS_FILE, create_empty_encodings, save_encodings

PROJECT_DIR = Path(__file__).resolve().parents[1]

if str(PROJECT_DIR) not in sys.path:
    sys.path.append(str(PROJECT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def setup_django():
    if apps.ready:
        return

    import django

    django.setup()


def encode_students(output_file: Path = ENCODINGS_FILE):
    setup_django()

    from students.models import Student

    data = create_empty_encodings()

    students = Student.objects.filter(is_active=True).exclude(photo="").exclude(photo__isnull=True)

    for student in students:
        if not student.photo or not Path(student.photo.path).exists():
            print(f"Bo qua {student}: khong tim thay anh.")
            continue

        try:
            image = np.array(Image.open(student.photo.path).convert("RGB"), dtype=np.uint8)
            image = np.ascontiguousarray(image, dtype=np.uint8)
            face_locations = face_recognition.face_locations(image, model="hog")
            face_encodings = face_recognition.face_encodings(image, face_locations)
        except Exception as exc:
            print(f"Bo qua {student}: loi xu ly anh ({exc}).")
            continue

        if not face_encodings:
            print(f"Bo qua {student}: khong tim thay khuon mat.")
            continue

        if len(face_encodings) > 1:
            print(f"{student}: tim thay nhieu khuon mat, lay khuon mat dau tien.")

        encoding = face_encodings[0]
        if len(encoding) != 128:
            print(f"Bo qua {student}: vector khong phai 128 chieu.")
            continue

        data["encodings"].append(encoding)
        data["student_ids"].append(student.student_id)
        data["names"].append(student.full_name)
        print(f"Da encode: {student.student_id} - {student.full_name}")

    save_encodings(data, output_file)

    print(f"Da luu {len(data['encodings'])} vector vao {output_file}")
    return data


if __name__ == "__main__":
    encode_students()
