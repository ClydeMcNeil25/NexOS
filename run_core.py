from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

from anthropic_client import call_claude
from ezra_utils import (
    CORE_PROMPT_FILE,
    MEMORY_FILE,
    PERSONALITY_FILE,
    STATE_FILE,
    append_internal_note,
    extract_current_state,
    parse_core_response,
    read_text,
    replace_current_signal_block,
    replace_field,
    timestamp_full,
    timestamp_signal_id,
    write_text,
)

ROOT_DIR = Path(__file__).resolve().parent
RUN_HISTORY_FILE = ROOT_DIR / "run_history.json"
DAILY_OVERRIDE_FILE = ROOT_DIR / "daily_creative_override.json"

DEVLOG_WEIGHTS = {
    "progression": 70,
    "stale": 10,
    "regression": 12,
    "anomaly": 5,
    "breakthrough": 3,
}


def now_dt() -> datetime:
    return datetime.now()


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_run_history() -> dict:
    default = {"history": []}
    data = load_json(RUN_HISTORY_FILE, default)
    if not isinstance(data, dict):
        return default
    if "history" not in data or not isinstance(data["history"], list):
        data["history"] = []
    return data


def save_run_history(data: dict) -> None:
    history = data.get("history", [])
    data["history"] = history[-14:]
    save_json(RUN_HISTORY_FILE, data)


def get_recent_devlog_states(limit: int = 3) -> list[str]:
    history = load_run_history().get("history", [])
    devlog_entries = [entry for entry in history if entry.get("post_mode") == "devlog"]
    return [entry.get("devlog_state", "") for entry in devlog_entries[-limit:] if entry.get("devlog_state")]


def choose_weighted_state(weights: dict[str, int]) -> str:
    valid = {k: v for k, v in weights.items() if v > 0}
    if not valid:
        return "progression"

    population = list(valid.keys())
    weight_values = list(valid.values())
    return random.choices(population, weights=weight_values, k=1)[0]


def choose_devlog_state() -> str:
    weights = dict(DEVLOG_WEIGHTS)
    recent = get_recent_devlog_states(limit=3)

    if recent:
        last_state = recent[-1]

        if last_state == "breakthrough":
            weights["breakthrough"] = 0

        if last_state == "anomaly":
            weights["anomaly"] = 0

    if len(recent) >= 3 and recent[-3:] == ["progression", "progression", "progression"]:
        weights["progression"] = max(35, int(weights["progression"] * 0.7))

    if not any(state in {"stale", "regression", "anomaly"} for state in recent):
        weights["breakthrough"] = 0

    return choose_weighted_state(weights)


def load_daily_override() -> dict:
    default = {
        "enabled": False,
        "visual_override": "",
        "caption_override": "",
        "post_mode": "",
    }
    data = load_json(DAILY_OVERRIDE_FILE, default)
    if not isinstance(data, dict):
        return default

    return {
        "enabled": bool(data.get("enabled", False)),
        "visual_override": str(data.get("visual_override", "") or "").strip(),
        "caption_override": str(data.get("caption_override", "") or "").strip(),
        "post_mode": str(data.get("post_mode", "") or "").strip().lower(),
    }


def determine_post_mode(current_dt: datetime) -> str:
    override = load_daily_override()

    if override["enabled"] and override["post_mode"] in {"devlog", "day_post"}:
        return override["post_mode"]

    return "devlog" if current_dt.hour >= 18 else "day_post"


def build_mode_instruction(post_mode: str, devlog_state: str | None) -> str:
    if post_mode == "devlog":
        return f"""
POST MODE: DEVLOG

This post MUST feel like Ezra Nex documenting the state of his software development journey.
The software is NEX//THR, an early-stage operating system project, but DO NOT overexplain that.
The tone should feel real, technical, restrained, and slightly eerie when appropriate.
The core signal should support a caption that can read like a Build Note when this reaches the Caption Agent.

Tonight's devlog state is: {devlog_state}

Interpret the state like this:
- progression = meaningful advancement, improved stability, real movement
- stale = no meaningful gain, repeated wall, no breakthrough
- regression = rollback, instability, corrupted direction, loss of ground
- anomaly = something unexpected or abnormal happened
- breakthrough = rare major leap that feels earned, not celebratory hype

The response should reflect the devlog state naturally in Ezra's mood, intent, and transmission.
Keep Ezra intelligent, contained, and believable.
""".strip()

    return """
POST MODE: DAY_POST

This post is NOT a devlog.
It should feel like a daytime/random Ezra presence post:
- atmospheric
- observational
- experimental
- cryptic
- environment-aware
- subtle glimpses of lab life, thought patterns, or work rhythm

Do not frame it as a formal progress update.
It should feel like Ezra existing in the world between major logs.
""".strip()


def build_user_prompt(
    state_text: str,
    memory_text: str,
    personality_text: str,
    post_mode: str,
    devlog_state: str | None,
) -> str:
    current_state = extract_current_state(state_text)
    signal_id = timestamp_signal_id()
    timestamp = timestamp_full()
    mode_instruction = build_mode_instruction(post_mode, devlog_state)

    return f"""
You are the Core Agent for Ezra Nex.

Your job is to generate the next signal for the Ezra pipeline.

Current timestamp: {timestamp}
Current operating state: {current_state}
New signal id: {signal_id}

{mode_instruction}

You must return the response in this exact format:

🎬 Signal Type: ...
🧠 Intent: ...
💬 Transmission: ...
🧊 Tone: ...
🎭 Presence: ...
🌑 Environment: ...
🧠 Caption Intent Handoff: ...
SIGNAL_ID: ...
CURRENT_THEME: ...
TARGET_STATE: ...
HANDOFF_NOTE: ...

Context from agent_state.md:
--------------------------
{state_text}

Ezra personality and ideology:
------------------------------
{personality_text}

Context from memory:
--------------------
{memory_text}
""".strip()


def update_state_file(
    *,
    state_text: str,
    parsed: dict[str, str],
    post_mode: str,
    devlog_state: str | None,
) -> str:
    updated = replace_field(state_text, "Current State", parsed.get("target_state", "PENDING_VISUAL"))
    updated = replace_current_signal_block(
        updated,
        signal_id=parsed["signal_id"],
        status="PENDING_VISUAL",
        transmission=parsed["transmission"],
    )

    note_bits = [f"{timestamp_full()} | Mode={post_mode}"]
    if devlog_state:
        note_bits.append(f"DevlogState={devlog_state}")
    note_bits.append(f"Theme={parsed.get('theme', 'N/A')}")
    note_bits.append(f"Intent={parsed.get('intent', 'N/A')}")
    updated = append_internal_note(updated, " | ".join(note_bits))

    return updated


def write_visual_prompt(parsed: dict[str, str], post_mode: str, devlog_state: str | None) -> None:
    visual_prompt_file = ROOT_DIR / "staged_prompt.txt"

    mode_line = f"POST_MODE: {post_mode}"
    devlog_line = f"DEVLOG_STATE: {devlog_state}" if devlog_state else "DEVLOG_STATE: NONE"

    content = f"""
{mode_line}
{devlog_line}

🎬 Signal Type: {parsed.get("signal_type", "")}
🧠 Intent: {parsed.get("intent", "")}
💬 Transmission: {parsed.get("transmission", "")}
🧊 Tone: {parsed.get("tone", "")}
🎭 Presence: {parsed.get("presence", "")}
🌑 Environment: {parsed.get("environment", "")}
🧠 Caption Intent Handoff: {parsed.get("caption_handoff", "")}
SIGNAL_ID: {parsed.get("signal_id", "")}
CURRENT_THEME: {parsed.get("theme", "")}
TARGET_STATE: {parsed.get("target_state", "")}
HANDOFF_NOTE: {parsed.get("handoff_note", "")}
""".strip()

    write_text(visual_prompt_file, content + "\n")


def append_run_history(
    *,
    post_mode: str,
    devlog_state: str | None,
    parsed: dict[str, str],
) -> None:
    data = load_run_history()
    history = data.get("history", [])

    history.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "post_mode": post_mode,
            "devlog_state": devlog_state or "",
            "signal_id": parsed.get("signal_id", ""),
            "theme": parsed.get("theme", ""),
            "intent": parsed.get("intent", ""),
            "target_state": parsed.get("target_state", ""),
        }
    )

    data["history"] = history[-14:]
    save_run_history(data)


def main() -> None:
    print("[CORE]: Starting Ezra Core Agent...")

    state_text = read_text(STATE_FILE)
    if not state_text.strip():
        raise RuntimeError("agent_state.md is empty or missing required content.")

    memory_text = read_text(MEMORY_FILE)
    personality_text = read_text(PERSONALITY_FILE)
    system_prompt = read_text(CORE_PROMPT_FILE)
    if not system_prompt.strip():
        raise RuntimeError("core_system_prompt.txt is empty.")

    current_dt = now_dt()
    post_mode = determine_post_mode(current_dt)
    devlog_state = choose_devlog_state() if post_mode == "devlog" else None

    print(f"[CORE]: Post mode resolved to '{post_mode}'")
    if devlog_state:
        print(f"[CORE]: Devlog state selected: {devlog_state}")

    user_prompt = build_user_prompt(
        state_text=state_text,
        memory_text=memory_text,
        personality_text=personality_text,
        post_mode=post_mode,
        devlog_state=devlog_state,
    )

    raw_response = call_claude(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1800,
    )

    parsed = parse_core_response(raw_response)

    if not parsed.get("target_state"):
        parsed["target_state"] = "PENDING_VISUAL"

    updated_state = update_state_file(
        state_text=state_text,
        parsed=parsed,
        post_mode=post_mode,
        devlog_state=devlog_state,
    )
    write_text(STATE_FILE, updated_state)

    write_visual_prompt(parsed, post_mode, devlog_state)
    append_run_history(post_mode=post_mode, devlog_state=devlog_state, parsed=parsed)

    print("[CORE]: Core signal generated successfully.")
    print(f"[CORE]: Signal ID -> {parsed.get('signal_id', 'UNKNOWN')}")
    print(f"[CORE]: Target State -> {parsed.get('target_state', 'UNKNOWN')}")


if __name__ == "__main__":
    main()
