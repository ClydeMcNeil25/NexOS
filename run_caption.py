from __future__ import annotations

import json
from pathlib import Path

from anthropic_client import call_claude
from ezra_utils import (
    CAPTION_SYSTEM_PROMPT_FILE,
    FINAL_CAPTION_FILE,
    MEMORY_FILE,
    STATE_FILE,
    append_internal_note,
    append_text,
    extract_current_state,
    extract_signal_id,
    parse_caption_response,
    read_text,
    replace_field,
    require_file,
    timestamp_full,
    timestamp_time,
    write_text,
)


ROOT_DIR = Path(__file__).resolve().parent
CREATIVE_OVERRIDE_FILE = ROOT_DIR / "daily_creative_override.json"
RUN_HISTORY_FILE = ROOT_DIR / "run_history.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_caption_override() -> str:
    default = {
        "enabled": False,
        "post_mode": "",
        "visual_override": "",
        "caption_override": "",
    }
    data = load_json(CREATIVE_OVERRIDE_FILE, default)
    if not isinstance(data, dict):
        return ""
    if not data.get("enabled", False):
        return ""
    return str(data.get("caption_override", "") or "").strip()


def load_run_history() -> dict:
    default = {"history": []}
    data = load_json(RUN_HISTORY_FILE, default)
    if not isinstance(data, dict):
        return default
    if "history" not in data or not isinstance(data["history"], list):
        data["history"] = []
    return data


def get_signal_context(signal_id: str) -> dict:
    history = load_run_history().get("history", [])
    for entry in reversed(history):
        if entry.get("signal_id") == signal_id:
            return entry
    return {}


def build_context_block(signal_context: dict) -> str:
    post_mode = str(signal_context.get("post_mode", "") or "").strip()
    devlog_state = str(signal_context.get("devlog_state", "") or "").strip()
    theme = str(signal_context.get("theme", "") or "").strip()
    intent = str(signal_context.get("intent", "") or "").strip()

    lines = []

    if post_mode:
        lines.append(f"Post Mode: {post_mode}")
    if devlog_state:
        lines.append(f"Devlog State: {devlog_state}")
    if theme:
        lines.append(f"Theme: {theme}")
    if intent:
        lines.append(f"Intent: {intent}")

    if not lines:
        return "No recent signal context found."

    return "\n".join(lines)


def build_mode_guidance(signal_context: dict) -> str:
    post_mode = str(signal_context.get("post_mode", "") or "").strip().lower()
    devlog_state = str(signal_context.get("devlog_state", "") or "").strip().lower()

    if post_mode == "devlog":
        guidance = [
            "This is a DEVLOG caption.",
            "The caption should feel like Ezra is documenting the current state of a real software build cycle.",
            "It should be concise, believable, restrained, and slightly cold.",
            "Do not sound like marketing copy. Do not sound inspirational. Do not overexplain.",
        ]

        if devlog_state == "progression":
            guidance.append("Tone target: controlled confidence, measurable movement, no hype.")
        elif devlog_state == "stale":
            guidance.append("Tone target: quiet frustration, repetition, stalled momentum.")
        elif devlog_state == "regression":
            guidance.append("Tone target: controlled irritation, rollback, instability, doubt.")
        elif devlog_state == "anomaly":
            guidance.append("Tone target: curiosity with unease, something behaved differently.")
        elif devlog_state == "breakthrough":
            guidance.append("Tone target: rare calm clarity, earned success, no celebration.")

        return "\n".join(guidance)

    return "\n".join(
        [
            "This is a DAY POST caption.",
            "The caption should feel like Ezra existing between formal devlogs.",
            "Favor atmosphere, observation, cryptic thought, or quiet technical presence.",
            "Do not frame it like a milestone update unless explicitly forced.",
        ]
    )


def build_override_block(caption_override: str) -> str:
    if not caption_override:
        return ""
    return f"""
Manual Caption Override:
{caption_override}
""".rstrip()


def build_user_prompt(
    state_text: str,
    memory_text: str,
    signal_context: dict,
) -> str:
    signal_id = extract_signal_id(state_text)
    caption_override = load_caption_override()
    signal_context_block = build_context_block(signal_context)
    mode_guidance = build_mode_guidance(signal_context)
    override_block = build_override_block(caption_override)

    return f"""
You are executing the Ezra Nex Caption Agent in a headless automation pipeline.

Your job:
- Read the state, memory, and signal context
- Generate ONE final caption only
- Output ONLY the caption text
- No labels
- No quotation marks unless they are naturally part of the caption
- No explanation
- No bullet points

Caption rules:
- keep it concise
- keep it believable
- keep it restrained
- Ezra is intelligent, controlled, and emotionally compressed
- avoid generic social media phrasing
- avoid sounding cheerful or promotional
- subtle ambiguity is good
- the caption should feel like a real post from Ezra, not a narrator summary

Signal context:
{signal_context_block}

Mode guidance:
{mode_guidance}

{override_block}

Signal ID: {signal_id}

=== CURRENT STATE FILE ===
{state_text}

=== MEMORY FILE ===
{memory_text}
""".strip()


def main() -> int:
    require_file(STATE_FILE)
    require_file(CAPTION_SYSTEM_PROMPT_FILE)
    require_file(RUN_HISTORY_FILE)

    state_text = read_text(STATE_FILE)
    current_state = extract_current_state(state_text)
    signal_id = extract_signal_id(state_text)

    if current_state != "PENDING_CAPTION":
        print(f"[SYSTEM_WAIT]: Awaiting state PENDING_CAPTION. Current state is {current_state}.")
        return 1

    memory_text = read_text(MEMORY_FILE)
    system_prompt = read_text(CAPTION_SYSTEM_PROMPT_FILE)
    signal_context = get_signal_context(signal_id)

    user_prompt = build_user_prompt(
        state_text=state_text,
        memory_text=memory_text,
        signal_context=signal_context,
    )

    raw_caption = call_claude(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=400,
    )

    final_caption = parse_caption_response(raw_caption)
    write_text(FINAL_CAPTION_FILE, final_caption + "\n")

    state_text = replace_field(state_text, "Current State", "IDLE")
    state_text = replace_field(state_text, "Last Update", timestamp_full())
    state_text = append_internal_note(
        state_text,
        f"[{timestamp_time()}] Caption Agent: Caption finalized (ID: {signal_id})",
    )
    write_text(STATE_FILE, state_text)

    append_text(
        MEMORY_FILE,
        (
            f"\n[CAPTION_LOG]: {timestamp_full()} | Status: FINALIZED | "
            f"ID: {signal_id} | Caption: {final_caption}\n"
        ),
    )

    print(f"[CAPTION]: OK | ID={signal_id} | TARGET=IDLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
