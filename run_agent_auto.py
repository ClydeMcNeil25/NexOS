from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
RUN_HISTORY_FILE = ROOT_DIR / "run_history.json"
LOCK_FILE = ROOT_DIR / "ezra_auto.lock"
BATCH_FILE = ROOT_DIR / "run_agent_silent.bat"

DEVLOG_HOUR = 21  # 9 PM
DAY_POST_START_HOUR = 10  # 10 AM
DAY_POST_END_HOUR = 18    # before 6 PM
LOCK_TIMEOUT_MINUTES = 30


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
    data["history"] = history[-30:]
    save_json(RUN_HISTORY_FILE, data)


def now_dt() -> datetime:
    return datetime.now()


def today_str() -> str:
    return now_dt().strftime("%Y-%m-%d")


def read_lock_data() -> dict:
    default = {}
    if not LOCK_FILE.exists():
        return default
    return load_json(LOCK_FILE, default)


def is_stale_lock(lock_data: dict) -> bool:
    started_at = str(lock_data.get("started_at", "") or "").strip()
    if not started_at:
        return True

    try:
        started_dt = datetime.strptime(started_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return True

    return now_dt() - started_dt > timedelta(minutes=LOCK_TIMEOUT_MINUTES)


def is_locked() -> bool:
    if not LOCK_FILE.exists():
        return False

    lock_data = read_lock_data()
    if is_stale_lock(lock_data):
        print("[AUTO]: Stale lock detected. Removing it automatically.")
        remove_lock()
        return False

    return True


def create_lock() -> None:
    LOCK_FILE.write_text(
        json.dumps(
            {
                "started_at": now_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "pid_hint": "ezra_auto",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def remove_lock() -> None:
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def get_today_entries() -> list[dict]:
    history = load_run_history().get("history", [])
    today = today_str()
    results = []

    for entry in history:
        timestamp = str(entry.get("timestamp", "") or "")
        if timestamp.startswith(today):
            results.append(entry)

    return results


def already_completed_today(post_mode: str) -> bool:
    today_entries = get_today_entries()
    for entry in today_entries:
        if entry.get("event_type") == "automation_completion" and entry.get("post_mode") == post_mode:
            return True
    return False


def determine_desired_post_mode(current_dt: datetime) -> str | None:
    hour = current_dt.hour

    if hour >= DEVLOG_HOUR:
        if already_completed_today("devlog"):
            return None
        return "devlog"

    if DAY_POST_START_HOUR <= hour < DAY_POST_END_HOUR:
        if already_completed_today("day_post"):
            return None
        return "day_post"

    return None


def update_override(post_mode: str) -> None:
    override_path = ROOT_DIR / "daily_creative_override.json"

    default = {
        "enabled": False,
        "post_mode": "",
        "visual_override": "",
        "caption_override": "",
    }

    data = load_json(override_path, default)
    if not isinstance(data, dict):
        data = default.copy()

    data["enabled"] = True
    data["post_mode"] = post_mode
    data["visual_override"] = str(data.get("visual_override", "") or "")
    data["caption_override"] = str(data.get("caption_override", "") or "")

    save_json(override_path, data)


def reset_override() -> None:
    override_path = ROOT_DIR / "daily_creative_override.json"
    data = {
        "enabled": False,
        "post_mode": "",
        "visual_override": "",
        "caption_override": ""
    }
    save_json(override_path, data)


def append_automation_log(
    *,
    status: str,
    post_mode: str | None,
    note: str,
) -> None:
    data = load_run_history()
    history = data.get("history", [])

    history.append(
        {
            "timestamp": now_dt().strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "automation_completion" if status == "success" else "automation_event",
            "post_mode": post_mode or "",
            "status": status,
            "note": note,
        }
    )

    data["history"] = history[-30:]
    save_run_history(data)


def run_pipeline() -> int:
    if not BATCH_FILE.exists():
        raise FileNotFoundError(f"Missing launcher: {BATCH_FILE}")

    result = subprocess.run(
        ["cmd", "/c", str(BATCH_FILE)],
        cwd=str(ROOT_DIR),
        shell=False,
    )
    return int(result.returncode)


def main() -> int:
    print("[AUTO]: Ezra automation wrapper starting...")

    if is_locked():
        print("[AUTO]: Existing active lock detected. Aborting.")
        append_automation_log(
            status="skipped",
            post_mode=None,
            note="Skipped because active lock file already exists.",
        )
        return 1

    current_dt = now_dt()
    post_mode = determine_desired_post_mode(current_dt)

    if not post_mode:
        print("[AUTO]: Nothing scheduled to run right now.")
        append_automation_log(
            status="skipped",
            post_mode=None,
            note="No valid post window or today's target already completed.",
        )
        return 0

    print(f"[AUTO]: Resolved scheduled mode -> {post_mode}")

    create_lock()

    try:
        update_override(post_mode)

        code = run_pipeline()

        if code == 0:
            print(f"[AUTO]: {post_mode} run completed successfully.")
            append_automation_log(
                status="success",
                post_mode=post_mode,
                note=f"{post_mode} completed successfully.",
            )
            return 0

        print(f"[AUTO]: {post_mode} run failed with exit code {code}.")
        append_automation_log(
            status="failed",
            post_mode=post_mode,
            note=f"{post_mode} failed with exit code {code}.",
        )
        return code

    finally:
        reset_override()
        remove_lock()


if __name__ == "__main__":
    raise SystemExit(main())
