from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"

STATE_FILE = DATA_DIR / "agent_state.md"
MEMORY_FILE = DATA_DIR / "EN_MEM.txt"
DAILY_VISUAL_STATE_FILE = DATA_DIR / "daily_visual_state.json"
DAILY_CREATIVE_OVERRIDE_FILE = DATA_DIR / "daily_creative_override.json"
RUN_HISTORY_FILE = DATA_DIR / "run_history.json"

VISUAL_PROMPT_FILE = OUTPUT_DIR / "visual_prompt.txt"
FINAL_CAPTION_FILE = OUTPUT_DIR / "final_caption.txt"
STAGED_PROMPT_FILE = OUTPUT_DIR / "staged_prompt.txt"
RENDER_DEBUG_FILE = OUTPUT_DIR / "render_debug.json"
RENDER_MODE_FILE = OUTPUT_DIR / "render_mode.json"


def ensure_runtime_directories() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)
