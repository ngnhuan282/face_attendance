import time
from typing import Optional, Tuple

import cv2
import face_recognition
import numpy as np

try:
    from .face_detector import FaceDetector, draw_faces, open_webcam
    from .utils import ENCODINGS_FILE, load_encodings
except ImportError:
    from face_detector import FaceDetector, draw_faces, open_webcam
    from utils import ENCODINGS_FILE, load_encodings


def match_face(face_encoding, data, tolerance: float = 0.5) -> Tuple[Optional[str], Optional[float]]:
    known_encodings = data["encodings"]
    distances = face_recognition.face_distance(known_encodings, face_encoding)
    best_index = int(np.argmin(distances))
    best_distance = float(distances[best_index])

    if best_distance > tolerance:
        return None, best_distance

    student_id = data["student_ids"][best_index]
    name = data["names"][best_index]
    return f"{student_id} - {name}", best_distance


def recognize_from_webcam(
    camera_index: int = 0,
    tolerance: float = 0.5,
    print_cooldown: float = 3.0,
):
    data = load_encodings()
    detector = FaceDetector()
    webcam = open_webcam(camera_index)
    last_printed_at = {}

    print(f"Da nap {len(data['encodings'])} vector tu {ENCODINGS_FILE}")
    print("Dang mo webcam de nhan dien. Nhan 'q' de thoat.")

    try:
        while True:
            ok, frame = webcam.read()
            if not ok:
                print("Khong doc duoc frame tu webcam.")
                break

            face_locations = detector.detect_faces(frame)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            labels = []
            now = time.time()

            for face_encoding in face_encodings:
                name, distance = match_face(face_encoding, data, tolerance=tolerance)

                if name:
                    labels.append(name)
                    last_time = last_printed_at.get(name, 0)
                    if now - last_time >= print_cooldown:
                        print(f"Nhan dien: {name} (distance={distance:.3f})")
                        last_printed_at[name] = now
                else:
                    labels.append("Unknown")

            draw_faces(frame, face_locations, labels)
            cv2.imshow("Face Recognition", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        webcam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    recognize_from_webcam()
