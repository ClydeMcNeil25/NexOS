from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

STATE_FILE = ROOT_DIR / "agent_state.md"
MEMORY_FILE = ROOT_DIR / "EN_MEM.txt"
VISUAL_PROMPT_FILE = ROOT_DIR / "visual_prompt.txt"
FINAL_CAPTION_FILE = ROOT_DIR / "final_caption.txt"
CORE_PROMPT_FILE = ROOT_DIR / "core_system_prompt.txt"
VISUAL_SYSTEM_PROMPT_FILE = ROOT_DIR / "visual_system_prompt.txt"
CAPTION_SYSTEM_PROMPT_FILE = ROOT_DIR / "caption_system_prompt.txt"


def now_dt() -> datetime:
    return datetime.now()


def timestamp_full(dt: datetime | None = None) -> str:
    dt = dt or now_dt()
    return dt.strftime("%Y-%m-%d %I:%M %p")


def timestamp_time(dt: datetime | None = None) -> str:
    dt = dt or now_dt()
    return dt.strftime("%I:%M %p")


def timestamp_signal_id(dt: datetime | None = None) -> str:
    dt = dt or now_dt()
    return dt.strftime("%Y%m%d_%H%M%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def append_text(path: Path, content: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(content)


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")


def extract_current_state(state_text: str) -> str:
    match = re.search(r"\*\*Current State:\*\*\s*(.+)", state_text)
    if not match:
        raise ValueError("Could not find '**Current State:**' in agent_state.md")
    return match.group(1).strip()


def extract_signal_id(state_text: str) -> str:
    match = re.search(r"\*\*Signal ID:\*\*\s*(.+)", state_text)
    if not match:
        return "UNKNOWN_SIGNAL"
    return match.group(1).strip()


def replace_field(state_text: str, label: str, new_value: str) -> str:
    pattern = rf"(?m)^(\*\*{re.escape(label)}:\*\*\s*)(.*)$"
    if re.search(pattern, state_text):
        return re.sub(
            pattern,
            lambda m: f"{m.group(1)}{new_value}",
            state_text,
            count=1,
        )
    raise ValueError(f"Could not find field '{label}' in state file.")


def append_internal_note(state_text: str, note_line: str) -> str:
    marker = "## 🧠 INTERNAL TEAM NOTES"
    archive_marker = "## 📂 ARCHIVE"

    if marker not in state_text or archive_marker not in state_text:
        raise ValueError("State file structure is missing INTERNAL TEAM NOTES or ARCHIVE.")

    head, tail = state_text.split(marker, 1)
    notes_body, archive_and_after = tail.split(archive_marker, 1)
    notes_body = notes_body.rstrip() + f"\n* {note_line}\n\n"

    return head + marker + notes_body + archive_marker + archive_and_after


def replace_current_signal_block(
    state_text: str,
    *,
    signal_id: str,
    status: str,
    transmission: str,
) -> str:
    pattern = (
        r"## ⚡ CURRENT SIGNAL\s*"
        r"\*\*Signal ID:\*\*\s*.*?\n"
        r"\*\*Status:\*\*\s*.*?\n"
        r"\*\*Transmission:\*\*\s*.*?(?=\n---)"
    )

    replacement = (
        "## ⚡ CURRENT SIGNAL\n"
        f"**Signal ID:** {signal_id}\n"
        f"**Status:** {status}\n"
        f"**Transmission:** {transmission}"
    )

    if not re.search(pattern, state_text, flags=re.DOTALL):
        raise ValueError("Could not find CURRENT SIGNAL block in state file.")

    return re.sub(pattern, replacement, state_text, count=1, flags=re.DOTALL)


def archive_current_signal(state_text: str) -> str:
    current_signal_pattern = r"(## ⚡ CURRENT SIGNAL\s*.*?)(?=\n---)"
    match = re.search(current_signal_pattern, state_text, flags=re.DOTALL)

    if not match:
        raise ValueError("Could not find CURRENT SIGNAL block to archive.")

    current_signal_block = match.group(1).strip()

    state_without_signal = re.sub(
        current_signal_pattern,
        (
            "## ⚡ CURRENT SIGNAL\n"
            "**Signal ID:** [NONE]\n"
            "**Status:** Awaiting Core Agent Trigger\n"
            "**Transmission:** [NONE]"
        ),
        state_text,
        count=1,
        flags=re.DOTALL,
    )

    archive_marker = "## 📂 ARCHIVE"
    if archive_marker not in state_without_signal:
        raise ValueError("Could not find ARCHIVE section.")

    before_archive, archive_section = state_without_signal.split(archive_marker, 1)
    archive_section = archive_section.lstrip()

    if archive_section.startswith("* (Empty)"):
        archive_section = archive_section.replace("* (Empty)", f"- {current_signal_block}", 1)
    else:
        archive_section = f"- {current_signal_block}\n{archive_section}"

    return before_archive + archive_marker + "\n" + archive_section


def parse_core_response(raw_text: str) -> dict[str, str]:
    fields = {
        "signal_type": "",
        "intent": "",
        "transmission": "",
        "tone": "",
        "presence": "",
        "environment": "",
        "caption_handoff": "",
        "signal_id": "",
        "theme": "",
        "target_state": "",
        "handoff_note": "",
    }

    patterns = {
        "signal_type": r"🎬 Signal Type:\s*(.+)",
        "intent": r"🧠 Intent:\s*(.+)",
        "transmission": r"💬 Transmission:\s*(.+)",
        "tone": r"🧊 Tone:\s*(.+)",
        "presence": r"🎭 Presence:\s*(.+)",
        "environment": r"🌑 Environment:\s*(.+)",
        "caption_handoff": r"🧠 Caption Intent Handoff:\s*(.+)",
        "signal_id": r"SIGNAL_ID:\s*(.+)",
        "theme": r"CURRENT_THEME:\s*(.+)",
        "target_state": r"TARGET_STATE:\s*(.+)",
        "handoff_note": r"HANDOFF_NOTE:\s*(.+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, raw_text)
        if match:
            fields[key] = match.group(1).strip()

    if not fields["transmission"]:
        raise ValueError("Core response missing Transmission.")

    if not fields["signal_id"]:
        fields["signal_id"] = timestamp_signal_id()

    return fields


def parse_caption_response(raw_text: str) -> str:
    lines = [line.rstrip() for line in raw_text.strip().splitlines() if line.strip()]
    if not lines:
        raise ValueError("Caption response was empty.")
    return "\n".join(lines)
