from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.evidence import evidence_hash
from app.fingerprint import perceptual_hash, sha256_bytes
from app.face import detect_faces


def make_test_image() -> bytes:
    image = Image.new("RGB", (640, 480), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((140, 80, 500, 420), outline="black", width=4)
    draw.ellipse((240, 130, 400, 290), outline="black", width=5)
    draw.ellipse((285, 180, 305, 200), fill="black")
    draw.ellipse((335, 180, 355, 200), fill="black")
    draw.arc((280, 200, 360, 260), 0, 180, fill="black", width=4)

    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def main():
    data = make_test_image()
    print("SHA-256:", sha256_bytes(data))
    print("pHash:", perceptual_hash(data))

    result = detect_faces(data)
    print("Detected faces:", result["face_count"])

    evidence = {
        "schema": "prooflens/test",
        "image_sha256": sha256_bytes(data),
        "image_phash": perceptual_hash(data),
        "face_count": result["face_count"],
    }
    h1 = evidence_hash(evidence)
    evidence["face_count"] = 99
    h2 = evidence_hash(evidence)

    print("Hash before modification:", h1)
    print("Hash after modification :", h2)
    assert h1 != h2
    print("PASS: tamper changes evidence hash.")


if __name__ == "__main__":
    main()
