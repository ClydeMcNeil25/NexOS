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
WEBHOOK_TIMEOUT_SECONDS = 60


def load_environment() -> str:
    load_dotenv(ENV_FILE, override=True)
    return os.getenv("MAKE_WEBHOOK_URL", "").strip()


def latest_image() -> Path | None:
    if not IMAGES_DIR.exists():
        return None

    images = [path for path in IMAGES_DIR.glob("*.png") if path.is_file()]
    if not images:
        return None

    return max(images, key=lambda path: path.stat().st_mtime)


def build_form_fields(image_path: Path, caption: str) -> dict[str, str]:
    state_text = read_text(STATE_FILE)
    signal_id = extract_signal_id(state_text)

    return {
        "source": "ezra_nex",
        "signal_id": signal_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "caption": caption,
        "image_filename": image_path.name,
        "image_mime_type": "image/png",
        "metadata_json": json.dumps(
            {
                "state_file": STATE_FILE.name,
                "memory_file": MEMORY_FILE.name,
                "image_size_bytes": image_path.stat().st_size,
            }
        ),
    }


def build_legacy_json_payload(image_path: Path, caption: str) -> dict[str, object]:
    state_text = read_text(STATE_FILE)
    signal_id = extract_signal_id(state_text)

    return {
        "source": "ezra_nex",
        "signal_id": signal_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "caption": caption,
        "image_filename": image_path.name,
        "image_mime_type": "image/png",
        "metadata": {
            "state_file": STATE_FILE.name,
            "memory_file": MEMORY_FILE.name,
            "image_size_bytes": image_path.stat().st_size,
        },
    }


def main() -> int:
    webhook_url = load_environment()
    if not webhook_url:
        print("[WEBHOOK]: MAKE_WEBHOOK_URL not set. Skipping delivery.")
        return 0

    image_path = latest_image()
    if image_path is None:
        print("[WEBHOOK]: No rendered image found. Skipping delivery.")
        return 1

    caption = read_text(FINAL_CAPTION_FILE).strip()
    if not caption:
        print("[WEBHOOK]: final_caption.txt is empty. Skipping delivery.")
        return 1

    form_fields = build_form_fields(image_path, caption)
    legacy_payload = build_legacy_json_payload(image_path, caption)

    with image_path.open("rb") as image_file:
        response = requests.post(
            webhook_url,
            data={
                **form_fields,
                "payload_json": json.dumps(legacy_payload),
            },
            files={
                "image": (image_path.name, image_file, "image/png"),
            },
            timeout=WEBHOOK_TIMEOUT_SECONDS,
        )
    response.raise_for_status()

    print(f"[WEBHOOK]: Delivered {image_path.name} to Make webhook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
