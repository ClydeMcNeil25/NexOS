from __future__ import annotations

import os
import re
import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / ".env"
PROMPT_FILE = ROOT_DIR / "visual_prompt.txt"
IMAGES_DIR = ROOT_DIR / "Images"
PROFILE_IMAGE = ROOT_DIR / "Ezra Nex - Character Profile Sheet.png"

MODEL_NAME = "gemini-2.5-flash-image"

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350  # 4:5 ratio


def get_api_key() -> str:
    load_dotenv(ENV_FILE, override=True)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"Missing GEMINI_API_KEY or GOOGLE_API_KEY in {ENV_FILE}"
        )

    return api_key


# =========================
# DATE + INDEX SYSTEM
# =========================

def image_date_slug() -> str:
    return datetime.now().strftime("%d-%b-%Y").upper()


def image_time_slug() -> str:
    return datetime.now().strftime("%I-%M%p").lower()


def next_image_index(images_dir: Path) -> int:
    pattern = re.compile(r"^Ezra_(\d{4})_")
    max_index = -1

    for path in images_dir.glob("Ezra_*.png"):
        match = pattern.match(path.name)
        if match:
            max_index = max(max_index, int(match.group(1)))

    return max_index + 1


# =========================
# IMAGE PROCESSING
# =========================

def crop_to_4_5(img: Image.Image) -> Image.Image:
    width, height = img.size
    target_ratio = 4 / 5
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return img.crop((left, 0, left + new_width, height))

    new_height = int(width / target_ratio)
    top = (height - new_height) // 2
    return img.crop((0, top, width, top + new_height))


def extract_first_image(response) -> Image.Image:
    image_bytes = None
    text_parts: list[str] = []

    parts = getattr(response, "parts", None)
    if parts is None and getattr(response, "candidates", None):
        try:
            parts = response.candidates[0].content.parts
        except (AttributeError, IndexError, TypeError):
            parts = None

    for part in parts or []:
        text = getattr(part, "text", None)
        if text:
            text_parts.append(text)

        as_image = getattr(part, "as_image", None)
        if callable(as_image):
            try:
                image = as_image()
                if image is not None:
                    return image.convert("RGB")
            except Exception:
                pass

        inline_data = getattr(part, "inline_data", None)
        if inline_data is not None:
            data = getattr(inline_data, "data", None)
            if data:
                if isinstance(data, str):
                    data = base64.b64decode(data)
                image_bytes = data
                break

    if image_bytes is None:
        print_response_diagnostics(response)
        detail = " ".join(text_parts).strip()
        if detail:
            raise RuntimeError(f"Gemini returned no image parts. Text response: {detail}")
        raise RuntimeError("Gemini returned no image parts.")

    return Image.open(BytesIO(image_bytes)).convert("RGB")


def print_response_diagnostics(response) -> None:
    print("[RENDERER_DEBUG]: Gemini returned no image bytes.")
    print(f"[RENDERER_DEBUG]: Response type -> {type(response).__name__}")

    prompt_feedback = getattr(response, "prompt_feedback", None)
    if prompt_feedback is not None:
        print(f"[RENDERER_DEBUG]: prompt_feedback -> {prompt_feedback!r}")

    candidates = getattr(response, "candidates", None)
    print(f"[RENDERER_DEBUG]: candidates_count -> {len(candidates) if candidates else 0}")
    for index, candidate in enumerate(candidates or []):
        finish_reason = getattr(candidate, "finish_reason", None)
        safety_ratings = getattr(candidate, "safety_ratings", None)
        print(f"[RENDERER_DEBUG]: candidate[{index}].finish_reason -> {finish_reason!r}")
        if safety_ratings:
            print(f"[RENDERER_DEBUG]: candidate[{index}].safety_ratings -> {safety_ratings!r}")

        content = getattr(candidate, "content", None)
        cparts = getattr(content, "parts", None) or []
        print(f"[RENDERER_DEBUG]: candidate[{index}].parts_count -> {len(cparts)}")
        for part_index, part in enumerate(cparts):
            print(f"[RENDERER_DEBUG]: part[{part_index}] -> {part!r}")

    response_text = getattr(response, "text", None)
    if response_text:
        print(f"[RENDERER_DEBUG]: response.text -> {response_text}")


# =========================
# MAIN EXECUTION
# =========================

def main() -> int:
    api_key = get_api_key()

    print(f"[RENDERER]: Looking for prompt in {PROMPT_FILE}...")

    if not PROMPT_FILE.exists():
        print(f"[ERROR]: {PROMPT_FILE} not found! Did the Visual Agent run?")
        return 1

    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    if not prompt:
        print(f"[ERROR]: {PROMPT_FILE} is empty!")
        return 1

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("--- PROMPT DETECTED ---")
    print(prompt)
    print("-----------------------")

    client = genai.Client(api_key=api_key)

    base_instruction = (
        "The provided image is the canonical identity reference for Ezra Nex. "
        "Maintain the same person, facial structure, hairstyle, and identity across all generations. "
        "You may change outfit, pose, camera angle, lighting, and environment, "
        "but the identity must remain consistent with the reference image. "
        "Ezra's visual world must remain cold, controlled, desaturated, and emotionally distant. "
        "If outdoors, conditions should feel overcast, rainy, or post-rain rather than bright or cheerful. "
        "If in a cafe, the setting should feel isolated, subdued, and introspective rather than social or lively. "
        "Do not copy the reference image exactly. Generate a new scene with the same individual."
    )

    contents: list[types.Part | str] = [base_instruction]

    if PROFILE_IMAGE.exists():
        print(f"[RENDERER]: Using character reference image: {PROFILE_IMAGE.name}")
        contents.append(
            types.Part.from_bytes(
                data=PROFILE_IMAGE.read_bytes(),
                mime_type="image/png",
            )
        )
    else:
        print("[WARNING]: Character profile image not found. Proceeding without reference.")

    contents.append(prompt)

    print("[RENDERER]: Sending prompt + reference to Gemini image model...")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="4:5",
            ),
        ),
    )

    try:
        image = extract_first_image(response)
    except RuntimeError:
        if PROFILE_IMAGE.exists():
            print("[RENDERER]: Reference-based generation returned no image. Retrying prompt-only generation...")
            fallback_response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    base_instruction.replace("The provided image is", "Ezra Nex is")
                    + " No reference image is available for this retry.",
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio="4:5",
                    ),
                ),
            )
            image = extract_first_image(fallback_response)
        else:
            raise

    image = crop_to_4_5(image)
    image = image.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)

    image_index = next_image_index(IMAGES_DIR)
    date_slug = image_date_slug()
    time_slug = image_time_slug()

    output_path = IMAGES_DIR / f"Ezra_{image_index:04d}_{date_slug}_{time_slug}.png"
    image.save(output_path, format="PNG")

    print(f"[RENDERER]: Saved image -> {output_path.name}")
    print("[SYSTEM]: Image generation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

