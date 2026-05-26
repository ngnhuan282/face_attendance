from dataclasses import dataclass
import sys
from typing import Iterable, List, Tuple

import cv2
import face_recognition
import numpy as np

FaceLocation = Tuple[int, int, int, int]  # top, right, bottom, left


@dataclass
class FaceDetector:
    model: str = "hog"
    scale: float = 0.25

    def detect_faces(self, frame) -> List[FaceLocation]:
        if frame is None:
            return []

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)

        if self.scale != 1:
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=self.scale, fy=self.scale)
            small_frame = np.ascontiguousarray(small_frame, dtype=np.uint8)
        else:
            small_frame = rgb_frame

        small_locations = face_recognition.face_locations(small_frame, model=self.model)
        if self.scale == 1:
            return small_locations

        multiplier = int(1 / self.scale)
        return [
            (top * multiplier, right * multiplier, bottom * multiplier, left * multiplier)
            for top, right, bottom, left in small_locations
        ]


def open_webcam(camera_index: int = 0):
    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    webcam = cv2.VideoCapture(camera_index, backend)
    if not webcam.isOpened() and backend != cv2.CAP_ANY:
        webcam.release()
        webcam = cv2.VideoCapture(camera_index)
    if not webcam.isOpened():
        raise RuntimeError(f"Khong mo duoc webcam index {camera_index}")
    return webcam


def draw_faces(frame, face_locations: Iterable[FaceLocation], labels=None):
    labels = labels or []

    for index, (top, right, bottom, left) in enumerate(face_locations):
        label = labels[index] if index < len(labels) else "Face"

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 180, 0), 2)
        cv2.rectangle(frame, (left, bottom - 28), (right, bottom), (0, 180, 0), cv2.FILLED)
        cv2.putText(
            frame,
            label,
            (left + 6, bottom - 8),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1,
        )

    return frame


def preview_webcam_detection(camera_index: int = 0):
    detector = FaceDetector()
    webcam = open_webcam(camera_index)

    print("Dang mo webcam de detect khuon mat. Nhan 'q' de thoat.")
    try:
        while True:
            ok, frame = webcam.read()
            if not ok:
                print("Khong doc duoc frame tu webcam.")
                break

            face_locations = detector.detect_faces(frame)
            draw_faces(frame, face_locations)

            if face_locations:
                print(f"Detected {len(face_locations)} face(s)")

            cv2.imshow("Face Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        webcam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    preview_webcam_detection()
