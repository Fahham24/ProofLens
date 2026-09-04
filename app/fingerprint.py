from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image
import imagehash


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def perceptual_hash(data: bytes) -> str:
    image = Image.open(BytesIO(data)).convert("RGB")
    return str(imagehash.phash(image))


def phash_distance(hash_a: str, hash_b: str) -> int:
    return imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)


def phash_similarity(hash_a: str, hash_b: str) -> float:
    distance = phash_distance(hash_a, hash_b)
    # pHash is normally 64 bits. This converts Hamming distance to [0, 1].
    return max(0.0, 1.0 - (distance / 64.0))
