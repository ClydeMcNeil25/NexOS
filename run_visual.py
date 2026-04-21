from __future__ import annotations

import json
import random
from pathlib import Path

from anthropic_client import call_claude
from ezra_utils import (
    MEMORY_FILE,
    PERSONALITY_FILE,
    STATE_FILE,
    VISUAL_PROMPT_FILE,
    VISUAL_SYSTEM_PROMPT_FILE,
    append_internal_note,
    append_text,
    extract_current_state,
    extract_signal_id,
    read_text,
    replace_field,
    require_file,
    timestamp_full,
    timestamp_time,
    write_text,
)


ROOT_DIR = Path(__file__).resolve().parent
DAILY_VISUAL_STATE_FILE = ROOT_DIR / "daily_visual_state.json"
CREATIVE_OVERRIDE_FILE = ROOT_DIR / "daily_creative_override.json"
RUN_HISTORY_FILE = ROOT_DIR / "run_history.json"
RENDER_MODE_FILE = ROOT_DIR / "render_mode.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_visual_override() -> str:
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
    return str(data.get("visual_override", "") or "").strip()


def load_daily_visual_state() -> dict:
    require_file(DAILY_VISUAL_STATE_FILE)

    default = {
        "theme": "default",
        "outfit_id": "default_fit",
        "outfit_description": "dark minimalist technical outfit",
        "primary_environment": "system_core",
        "allowed_environments": ["system_core"],
    }

    data = load_json(DAILY_VISUAL_STATE_FILE, default)
    if not isinstance(data, dict):
        return default

    allowed = data.get("allowed_environments", ["system_core"])
    if not isinstance(allowed, list) or not allowed:
        allowed = ["system_core"]

    return {
        "theme": str(data.get("theme", "default") or "default").strip(),
        "outfit_id": str(data.get("outfit_id", "default_fit") or "default_fit").strip(),
        "outfit_description": str(
            data.get("outfit_description", "dark minimalist technical outfit")
            or "dark minimalist technical outfit"
        ).strip(),
        "primary_environment": str(
            data.get("primary_environment", "system_core") or "system_core"
        ).strip(),
        "allowed_environments": [str(item).strip() for item in allowed if str(item).strip()],
    }


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


def choose_environment(daily_state: dict) -> str:
    allowed = daily_state.get("allowed_environments", [])
    primary = daily_state.get("primary_environment", "")

    if not allowed:
        return primary or "system_core"

    weighted = list(allowed)
    if primary and primary in allowed:
        weighted.extend([primary, primary])

    return random.choice(weighted)


def build_context_block(signal_context: dict) -> str:
    post_mode = str(signal_context.get("post_mode", "") or "").strip()
    devlog_state = str(signal_context.get("devlog_state", "") or "").strip()
    content_type = str(signal_context.get("content_type", "") or "").strip()
    tension_stage = str(signal_context.get("tension_stage", "") or "").strip()
    theme = str(signal_context.get("theme", "") or "").strip()
    intent = str(signal_context.get("intent", "") or "").strip()

    lines = []

    if post_mode:
        lines.append(f"Post Mode: {post_mode}")

    if devlog_state:
        lines.append(f"Devlog State: {devlog_state}")

    if content_type:
        lines.append(f"Content Type: {content_type}")

    if tension_stage:
        lines.append(f"System Tension Stage: {tension_stage}")

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
    content_type = str(signal_context.get("content_type", "") or "").strip().lower()

    if content_type == "system_visual":
        return "\n".join(
            [
                "This is a SYSTEM VISUAL / OS VISUAL.",
                "The image must be UI-only or graphical.",
                "Do not include Ezra, a face, a body, hands, silhouette, or any human subject.",
                "Show NEX//THR through interface fragments, logs, state maps, diagnostic panels, node graphs, process flows, or partial system architecture.",
                "The design should feel leaked, controlled, incomplete, desaturated, and not product-marketing polished.",
                "Use blue-gray-black tones, slight imperfect alignment, partial readability, and subtle system tension.",
            ]
        )

    if content_type == "hybrid":
        return "\n".join(
            [
                "This is a HYBRID visual.",
                "Ezra should be present, but NEX//THR system elements must also be visible.",
                "Use screens, reflections, interface fragments, diagnostic logs, or subtle panels as secondary system evidence.",
                "Do not make the system elements flashy, magical, or product-like.",
            ]
        )

    if content_type == "silent":
        return "\n".join(
            [
                "This is a SILENT / NEAR-SILENT visual.",
                "The composition should be controlled, minimal, and unresolved.",
                "Reduce action, avoid explanation, and let environment behavior carry the tension.",
            ]
        )

    if post_mode == "devlog":
        guidance = [
            "This is a DEVLOG visual.",
            "The image should feel like a believable software-development moment in Ezra's life.",
            "It should support the sense that he is documenting real progress, friction, or instability around NEX//THR.",
            "Do not make it theatrical or overly sci-fi. Keep it grounded, technical, and cinematic.",
        ]

        if devlog_state == "progression":
            guidance.append("Visual energy: focused advancement, subtle confidence, stable momentum.")
        elif devlog_state == "stale":
            guidance.append("Visual energy: repetition, fatigue, stalled iteration, quiet frustration.")
        elif devlog_state == "regression":
            guidance.append("Visual energy: rollback, instability, tension, controlled irritation.")
        elif devlog_state == "anomaly":
            guidance.append("Visual energy: something slightly off, unusual behavior, subtle unease.")
        elif devlog_state == "breakthrough":
            guidance.append("Visual energy: rare earned success, calm clarity, no celebration or hype.")

        return "\n".join(guidance)

    return "\n".join(
        [
            "This is a DAY POST visual.",
            "The image should feel like Ezra existing in his world between formal devlogs.",
            "Favor atmosphere, observation, lab rhythm, quiet experimentation, or cryptic stillness.",
            "Do not frame the image like a major milestone update.",
        ]
    )


def build_override_block(visual_override: str) -> str:
    if not visual_override:
        return ""
    return f"""
Manual Visual Override:
{visual_override}
""".rstrip()


def build_hard_requirements(signal_context: dict) -> str:
    content_type = str(signal_context.get("content_type", "") or "").strip().lower()

    if content_type == "system_visual":
        return """
Hard requirements:
- vertical composition
- 4:5 aspect ratio
- graphical OS/interface visual
- no human subject
- no Ezra likeness
- no face, body, hands, silhouette, or person
- NEX//THR system interface fragments, logs, panels, state maps, node graphs, or process flows
- desaturated blue-gray-black palette
- subtle imperfect alignment
- not polished product marketing
- not a clean commercial UI mockup
- avoid bright colors unless explicitly forced by the override
""".strip()

    return """
Hard requirements:
- vertical composition
- 4:5 aspect ratio
- photorealistic
- cinematic lighting
- highly detailed skin texture
- exact Ezra likeness: dark hair, sharp features, clinical presence
- subject centered within the middle 80% of the frame
- enforce the same exact individual across all generations
- preserve daily outfit continuity
- preserve daily environmental continuity
- avoid bright colors unless explicitly forced by the override
""".strip()


def write_render_mode(signal_id: str, signal_context: dict) -> None:
    payload = {
        "signal_id": signal_id,
        "content_type": str(signal_context.get("content_type", "") or ""),
        "post_mode": str(signal_context.get("post_mode", "") or ""),
        "devlog_state": str(signal_context.get("devlog_state", "") or ""),
    }
    write_text(RENDER_MODE_FILE, json.dumps(payload, indent=2) + "\n")


def build_user_prompt(
    state_text: str,
    memory_text: str,
    personality_text: str,
    daily_state: dict,
    signal_context: dict,
) -> str:
    signal_id = extract_signal_id(state_text)
    content_type = str(signal_context.get("content_type", "") or "").strip().lower()
    selected_environment = "system_visual" if content_type == "system_visual" else choose_environment(daily_state)

    theme = daily_state.get("theme", "UNKNOWN_THEME")
    outfit_id = daily_state.get("outfit_id", "UNKNOWN_OUTFIT")
    outfit_description = daily_state.get("outfit_description", "")
    primary_environment = daily_state.get("primary_environment", "")
    allowed_environments = daily_state.get("allowed_environments", [])

    allowed_environments_text = ", ".join(allowed_environments) if allowed_environments else "system_core"
    visual_override = load_visual_override()
    signal_context_block = build_context_block(signal_context)
    mode_guidance = build_mode_guidance(signal_context)
    override_block = build_override_block(visual_override)
    hard_requirements = build_hard_requirements(signal_context)

    return f"""
You are executing the Ezra Nex Visual Agent in a headless automation pipeline.

Your job:
- Read the current state, memory, and signal context.
- Convert Ezra's current signal into ONE final image prompt paragraph only.
- Output ONLY the final image prompt paragraph.
- No labels. No bullet points. No commentary.

{hard_requirements}

Daily visual continuity:
- Theme: {theme}
- Outfit ID: {outfit_id}
- Outfit Description: {outfit_description}
- Primary Environment: {primary_environment}
- Allowed Environments: {allowed_environments_text}
- Selected Environment For This Post: {selected_environment}

Rules for outfit continuity:
- These rules do not apply to system_visual posts where Ezra is not present.
- Ezra must retain the same outfit identity throughout the day
- minor pose-related garment changes are allowed
- coat open or closed is allowed
- subtle layering visibility is allowed
- full outfit changes are NOT allowed
- color shifts are NOT allowed

Rules for environment:
- use the selected environment for this post
- do not invent an environment outside the allowed list unless the content type is system_visual
- if selected environment is system_visual, create a UI-only NEX//THR graphical system environment
- if selected environment is urban_exterior, it must feel rainy, overcast, post-rain, or muted
- if selected environment is isolated_cafe, Ezra must feel isolated and not socially engaged
- if selected environment is system_core, the environment should feel controlled, technical, and grounded

Signal context:
{signal_context_block}

Mode guidance:
{mode_guidance}

{override_block}

Ezra personality and ideology:
{personality_text}

Signal ID: {signal_id}

=== CURRENT STATE FILE ===
{state_text}

=== MEMORY FILE ===
{memory_text}
""".strip()


def main() -> int:
    require_file(STATE_FILE)
    require_file(VISUAL_SYSTEM_PROMPT_FILE)
    require_file(DAILY_VISUAL_STATE_FILE)
    require_file(RUN_HISTORY_FILE)

    state_text = read_text(STATE_FILE)
    current_state = extract_current_state(state_text)
    signal_id = extract_signal_id(state_text)

    if current_state != "PENDING_VISUAL":
        print(f"[SYSTEM_WAIT]: Awaiting state PENDING_VISUAL. Current state is {current_state}.")
        return 1

    memory_text = read_text(MEMORY_FILE)
    personality_text = read_text(PERSONALITY_FILE)
    system_prompt = read_text(VISUAL_SYSTEM_PROMPT_FILE)
    daily_state = load_daily_visual_state()
    signal_context = get_signal_context(signal_id)

    user_prompt = build_user_prompt(
        state_text=state_text,
        memory_text=memory_text,
        personality_text=personality_text,
        daily_state=daily_state,
        signal_context=signal_context,
    )

    visual_prompt = call_claude(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1400,
    ).strip()

    write_text(VISUAL_PROMPT_FILE, visual_prompt + "\n")
    write_render_mode(signal_id, signal_context)

    state_text = replace_field(state_text, "Current State", "PENDING_CAPTION")
    state_text = replace_field(state_text, "Last Update", timestamp_full())
    state_text = append_internal_note(
        state_text,
        f"[{timestamp_time()}] Visual Agent: Prompt staged (ID: {signal_id})",
    )
    write_text(STATE_FILE, state_text)

    append_text(
        MEMORY_FILE,
        (
            f"\n[VISUAL_LOG]: {timestamp_full()} | Status: PROMPT_STAGED | "
            f"ID: {signal_id} | Outfit: {daily_state.get('outfit_id', 'N/A')} | "
            f"PrimaryEnv: {daily_state.get('primary_environment', 'N/A')}\n"
        ),
    )

    print(
        f"[VISUAL]: OK | ID={signal_id} | TARGET=PENDING_CAPTION | "
        f"OUTFIT={daily_state.get('outfit_id', 'N/A')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
