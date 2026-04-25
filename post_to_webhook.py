from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from ezra_utils import FINAL_CAPTION_FILE, MEMORY_FILE, STATE_FILE, extract_signal_id, read_text


ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / ".env"
IMAGES_DIR = ROOT_DIR / "Images"
GRAPH_API_BASE = "https://graph.facebook.com/v24.0"
FACEBOOK_TIMEOUT_SECONDS = 60


def load_environment() -> tuple[str, str]:
    load_dotenv(ENV_FILE, override=True)
    page_id = os.getenv("FACEBOOK_PAGE_ID", "").strip()
    page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    return page_id, page_access_token


def latest_image() -> Path | None:
    if not IMAGES_DIR.exists():
        return None

    images = [path for path in IMAGES_DIR.glob("*.png") if path.is_file()]
    if not images:
        return None

    return max(images, key=lambda path: path.stat().st_mtime)


def build_metadata(image_path: Path | None) -> dict[str, object]:
    state_text = read_text(STATE_FILE)
    signal_id = extract_signal_id(state_text)

    metadata: dict[str, object] = {
        "source": "ezra_nex",
        "signal_id": signal_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "state_file": STATE_FILE.name,
        "memory_file": MEMORY_FILE.name,
    }

    if image_path is not None:
        metadata["image_filename"] = image_path.name
        metadata["image_size_bytes"] = image_path.stat().st_size

    return metadata


def post_photo(
    *,
    page_id: str,
    page_access_token: str,
    image_path: Path,
    caption: str,
) -> requests.Response:
    endpoint = f"{GRAPH_API_BASE}/{page_id}/photos"
    with image_path.open("rb") as image_file:
        response = requests.post(
            endpoint,
            data={
                "caption": caption,
                "access_token": page_access_token,
            },
            files={
                "source": (image_path.name, image_file, "image/png"),
            },
            timeout=FACEBOOK_TIMEOUT_SECONDS,
        )
    return response


def post_text_fallback(
    *,
    page_id: str,
    page_access_token: str,
    caption: str,
) -> requests.Response:
    endpoint = f"{GRAPH_API_BASE}/{page_id}/feed"
    return requests.post(
        endpoint,
        data={
            "message": caption,
            "access_token": page_access_token,
        },
        timeout=FACEBOOK_TIMEOUT_SECONDS,
    )


def log_failure_context(image_path: Path | None, caption: str) -> None:
    metadata = build_metadata(image_path)
    print("[FACEBOOK]: Local outputs preserved after posting failure.")
    print(f"[FACEBOOK]: Metadata -> {json.dumps(metadata)}")
    print(f"[FACEBOOK]: Caption file -> {FINAL_CAPTION_FILE}")
    if image_path is not None:
        print(f"[FACEBOOK]: Image file -> {image_path}")
    print(f"[FACEBOOK]: Caption preview -> {caption}")


def main() -> int:
    page_id, page_access_token = load_environment()
    if not page_id or not page_access_token:
        print(
            "[FACEBOOK]: FACEBOOK_PAGE_ID and/or FACEBOOK_PAGE_ACCESS_TOKEN not set. "
            "Skipping direct Facebook posting."
        )
        return 0

    caption = read_text(FINAL_CAPTION_FILE).strip()
    if not caption:
        print("[FACEBOOK]: final_caption.txt is empty. Skipping direct Facebook posting.")
        return 1

    image_path = latest_image()
    if image_path is None:
        print("[FACEBOOK]: No rendered image found. Attempting text-only fallback post.")
        try:
            response = post_text_fallback(
                page_id=page_id,
                page_access_token=page_access_token,
                caption=caption,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[FACEBOOK]: Text-only fallback post failed: {exc}")
            log_failure_context(None, caption)
            return 1

        payload = response.json()
        print(f"[FACEBOOK]: Text-only post published successfully. Post ID -> {payload.get('id', 'UNKNOWN')}")
        return 0

    try:
        response = post_photo(
            page_id=page_id,
            page_access_token=page_access_token,
            image_path=image_path,
            caption=caption,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[FACEBOOK]: Photo post failed: {exc}")
        try:
            fallback_response = post_text_fallback(
                page_id=page_id,
                page_access_token=page_access_token,
                caption=caption,
            )
            fallback_response.raise_for_status()
        except requests.RequestException as fallback_exc:
            print(f"[FACEBOOK]: Text-only fallback also failed: {fallback_exc}")
            log_failure_context(image_path, caption)
            return 1

        fallback_payload = fallback_response.json()
        print(
            "[FACEBOOK]: Photo upload failed, but text-only fallback succeeded. "
            f"Post ID -> {fallback_payload.get('id', 'UNKNOWN')}"
        )
        print(f"[FACEBOOK]: Image preserved locally -> {image_path}")
        return 0

    payload = response.json()
    print(
        "[FACEBOOK]: Photo post published successfully. "
        f"Post ID -> {payload.get('post_id') or payload.get('id', 'UNKNOWN')}"
    )
    print(f"[FACEBOOK]: Image posted from -> {image_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
