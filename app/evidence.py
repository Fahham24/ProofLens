from __future__ import annotations

import hashlib
import json
import time
from typing import Any


def build_evidence(
    *,
    filename: str,
    image_sha256: str,
    image_phash: str,
    face_result: dict[str, Any],
    face_signature_result: dict[str, Any] | None,
    match: dict[str, Any] | None,
) -> dict[str, Any]:
    evidence = {
        "schema": "prooflens/evidence/v1",
        "created_at_unix": int(time.time()),
        "filename": filename,
        "privacy": {
            "raw_image_on_chain": False,
            "biometric_embedding_on_chain": False,
            "identity_inference": False,
        },
        "image": {
            "sha256": image_sha256,
            "phash": image_phash,
        },
        "face_detection": {
            "face_count": face_result["face_count"],
            "faces": face_result["faces"],
        },
        "face_encoding": face_signature_result,
        "reverse_image_match": match,
    }
    return evidence


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def evidence_hash(data: dict[str, Any]) -> str:
    canonical = canonical_json(data).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
