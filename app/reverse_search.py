from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from app.fingerprint import phash_similarity, perceptual_hash


SOCIAL_DOMAINS = {
    "instagram.com",
    "www.instagram.com",
    "facebook.com",
    "www.facebook.com",
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "tiktok.com",
    "www.tiktok.com",
    "linkedin.com",
    "www.linkedin.com",
    "pinterest.com",
    "www.pinterest.com",
    "threads.net",
    "www.threads.net",
    "youtube.com",
    "www.youtube.com",
}


@dataclass
class SearchCandidate:
    title: str
    source: str
    url: str
    image_url: str
    exact_match: bool
    similarity: float | None
    social: bool


class SerpApiLensProvider:
    """Genuine Google Lens search through SerpApi."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "SERPAPI_KEY is missing. Add it to .env to run a genuine reverse-image search."
            )
        self.api_key = api_key

    def search(self, image_bytes: bytes, filename: str = "upload.jpg") -> list[SearchCandidate]:
        upload_url = "https://serpapi.com/image"
        files = {
            "image": (
                filename,
                image_bytes,
                "application/octet-stream",
            )
        }
        response = requests.post(
            upload_url,
            params={"api_key": self.api_key},
            files=files,
            timeout=45,
        )
        response.raise_for_status()
        upload_data = response.json()

        if "error" in upload_data:
            raise RuntimeError(upload_data["error"])

        image_id = upload_data.get("image_id")
        if not image_id:
            raise RuntimeError("SerpApi did not return an image_id.")

        search_response = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_lens",
                "image_id": image_id,
                "api_key": self.api_key,
                "safe": "active",
                "no_cache": "true",
            },
            timeout=60,
        )
        search_response.raise_for_status()
        data = search_response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        candidates: list[SearchCandidate] = []
        for item in data.get("visual_matches", []):
            url = item.get("link") or ""
            image_url = item.get("image") or item.get("thumbnail") or ""
            if not url:
                continue

            candidates.append(
                SearchCandidate(
                    title=item.get("title") or "Untitled result",
                    source=item.get("source") or urlparse(url).netloc,
                    url=url,
                    image_url=image_url,
                    exact_match=bool(item.get("exact_matches", False)),
                    similarity=None,
                    social=is_social_url(url),
                )
            )

        return candidates[:20]


def is_social_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return host in SOCIAL_DOMAINS or any(
            host.endswith("." + domain) for domain in SOCIAL_DOMAINS
        )
    except Exception:
        return False


def score_candidates(
    image_bytes: bytes,
    candidates: list[SearchCandidate],
    max_downloads: int = 8,
) -> list[SearchCandidate]:
    """Download returned candidate images and score visual similarity with pHash."""
    source_hash = perceptual_hash(image_bytes)
    session = requests.Session()

    scored = []
    for candidate in candidates[:max_downloads]:
        if not candidate.image_url:
            scored.append(candidate)
            continue

        try:
            r = session.get(
                candidate.image_url,
                timeout=15,
                headers={"User-Agent": "ProofLens/1.0"},
            )
            r.raise_for_status()
            if len(r.content) > 5_000_000:
                raise ValueError("Candidate image is too large.")

            candidate_hash = perceptual_hash(r.content)
            candidate.similarity = round(
                phash_similarity(source_hash, candidate_hash), 4
            )
        except Exception:
            candidate.similarity = None

        scored.append(candidate)

    scored.sort(
        key=lambda x: (
            x.exact_match,
            x.similarity if x.similarity is not None else -1,
        ),
        reverse=True,
    )
    return scored
