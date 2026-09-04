from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np


CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def detect_faces(image_bytes: bytes) -> dict:
    """Detect faces locally. No image is sent to a face-recognition API."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode the uploaded image.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    boxes = []
    for (x, y, w, h) in faces:
        boxes.append(
            {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
            }
        )

    return {
        "image_width": int(image.shape[1]),
        "image_height": int(image.shape[0]),
        "face_count": len(boxes),
        "faces": boxes,
        "image": image,
    }


def face_signature(image: np.ndarray, box: dict) -> dict:
    """
    Create a compact, non-identifying visual signature.

    This is intentionally NOT a biometric identity embedding.
    It is a reproducible representation of the detected crop for
    demonstrating the encoding step.
    """
    x, y = box["x"], box["y"]
    w, h = box["width"], box["height"]

    crop = image[y:y+h, x:x+w]
    if crop.size == 0:
        raise ValueError("Detected face crop is empty.")

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    normalized = cv2.resize(gray, (16, 16), interpolation=cv2.INTER_AREA)
    normalized = cv2.equalizeHist(normalized)

    vector = (normalized.astype(np.float32) / 255.0).flatten()
    vector = (vector - float(vector.mean())) / (float(vector.std()) + 1e-8)

    raw = vector.astype("<f4").tobytes()
    signature_hash = hashlib.sha256(raw).hexdigest()

    return {
        "dimensions": int(vector.size),
        "signature_sha256": signature_hash,
        "vector_preview": [round(float(v), 4) for v in vector[:12]],
    }


def annotate_faces(image: np.ndarray, boxes: list[dict]) -> np.ndarray:
    output = image.copy()
    for i, box in enumerate(boxes, start=1):
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        cv2.rectangle(output, (x, y), (x+w, y+h), (0, 255, 0), 3)
        cv2.putText(
            output,
            f"Face {i}",
            (x, max(30, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    return cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
