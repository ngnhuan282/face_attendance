import os
import pickle
import tempfile
from pathlib import Path


ENCODINGS_FILE = Path(__file__).resolve().parent / "encodings.pkl"


def create_empty_encodings():
    return {
        "encodings": [],
        "student_ids": [],
        "names": [],
    }


def save_encodings(data, encodings_file: Path = ENCODINGS_FILE):
    encodings_file.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("wb", delete=False, dir=encodings_file.parent) as file:
        pickle.dump(data, file)
        temp_name = file.name

    os.replace(temp_name, encodings_file)

    return encodings_file


def load_encodings(encodings_file: Path = ENCODINGS_FILE, require_data: bool = True):
    if not encodings_file.exists():
        raise FileNotFoundError(
            f"Khong tim thay {encodings_file}. Hay chay face_encoder.py truoc."
        )

    with encodings_file.open("rb") as file:
        data = pickle.load(file)

    if require_data and not data.get("encodings"):
        raise ValueError("encodings.pkl khong co vector khuon mat nao.")

    return data
