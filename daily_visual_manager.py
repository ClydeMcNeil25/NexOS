from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DAILY_VISUAL_STATE_FILE = ROOT_DIR / "daily_visual_state.json"


TODAY_POOLS = [
    {
        "theme": "infrastructure_day",
        "outfit_id": "infra_black_001",
        "outfit_description": (
            "tailored black high-collar coat, dark charcoal inner layer, "
            "minimal structured silhouette, matte textures, no bright colors"
        ),
        "primary_environment": "data_vault",
        "allowed_environments": [
            "data_vault",
            "dark_lab",
            "system_core",
            "surveillance_room"
        ],
    },
    {
        "theme": "urban_detachment_day",
        "outfit_id": "urban_coat_001",
        "outfit_description": (
            "dark tailored overcoat, black inner layers, structured minimal styling, "
            "clean lines, subdued materials, no bright colors"
        ),
        "primary_environment": "urban_exterior",
        "allowed_environments": [
            "urban_exterior",
            "isolated_cafe",
            "surveillance_room"
        ],
    },
    {
        "theme": "executive_control_day",
        "outfit_id": "executive_black_001",
        "outfit_description": (
            "tailored black suit or structured formalwear, dark shirt layer, "
            "minimalist luxury, sharp silhouette, fully desaturated palette"
        ),
        "primary_environment": "executive_hall",
        "allowed_environments": [
            "executive_hall",
            "data_vault",
            "isolated_cafe"
        ],
    },
]


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_existing() -> dict:
    if not DAILY_VISUAL_STATE_FILE.exists():
        return {}
    try:
        return json.loads(DAILY_VISUAL_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    DAILY_VISUAL_STATE_FILE.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    today = today_str()
    existing = load_existing()

    if existing.get("date") == today:
        print(
            "[DAILY_VISUAL]: Existing daily visual state found "
            f"for {today} | outfit={existing.get('outfit_id', 'UNKNOWN')}"
        )
        return 0

    selected = random.choice(TODAY_POOLS)

    state = {
        "date": today,
        "theme": selected["theme"],
        "outfit_id": selected["outfit_id"],
        "outfit_description": selected["outfit_description"],
        "primary_environment": selected["primary_environment"],
        "allowed_environments": selected["allowed_environments"],
    }

    save_state(state)

    print(
        "[DAILY_VISUAL]: New daily visual state created "
        f"for {today} | theme={state['theme']} | outfit={state['outfit_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
