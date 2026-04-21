from __future__ import annotations

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

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


def build_payload(image_path: Path, caption: str) -> dict[str, Any]:
    state_text = read_text(STATE_FILE)
    signal_id = extract_signal_id(state_text)
    image_bytes = image_path.read_bytes()

    return {
        "source": "ezra_nex",
        "signal_id": signal_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "caption": caption,
        "image_filename": image_path.name,
        "image_mime_type": "image/png",
        "image_base64": base64.b64encode(image_bytes).decode("ascii"),
        "metadata": {
            "state_file": STATE_FILE.name,
            "memory_file": MEMORY_FILE.name,
            "image_size_bytes": len(image_bytes),
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

    payload = build_payload(image_path, caption)
    response = requests.post(webhook_url, json=payload, timeout=WEBHOOK_TIMEOUT_SECONDS)
    response.raise_for_status()

    print(f"[WEBHOOK]: Delivered {image_path.name} to Make webhook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
