import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

# Silence APScheduler logs unless needed
logging.getLogger("apscheduler").setLevel(logging.WARNING)

REMINDERS_FILE = "data/reminders.json"

# ── Singleton scheduler ───────────────────────────────────────────────────────
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get or start the background scheduler (singleton)"""
    global _scheduler
    if _scheduler is None or not _scheduler.running:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
        print("[ReminderScheduler] Background scheduler started.")
        # Reload persisted reminders on startup
        _reschedule_persisted()
    return _scheduler


# ── Persistence ───────────────────────────────────────────────────────────────

def _load_reminders() -> list:
    path = Path(REMINDERS_FILE)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def _save_reminders(reminders: list):
    Path(REMINDERS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2, default=str)


def _next_id(reminders: list) -> str:
    ids = [int(r["id"].replace("reminder_", "")) for r in reminders if r["id"].startswith("reminder_")]
    return f"reminder_{max(ids) + 1 if ids else 1}"


# ── Delivery callback ─────────────────────────────────────────────────────────

def _fire_reminder(reminder_id: str):
    """Called by APScheduler when a reminder is due"""
    reminders = _load_reminders()
    reminder = next((r for r in reminders if r["id"] == reminder_id), None)
    if not reminder:
        return

    message = f"⏰ REMINDER: {reminder['title']}\n{reminder.get('note', '')}"
    print(f"\n{message}\n")

    # Email delivery
    if reminder.get("email"):
        try:
            from tools.send_mail_tool import send_email
            send_email(
                to=reminder["email"],
                subject=f"⏰ Reminder: {reminder['title']}",
                body=f"{reminder['title']}\n\n{reminder.get('note', '')}\n\nScheduled for: {reminder['fire_at']}",
            )
            print(f"[ReminderScheduler] Email sent to {reminder['email']}")
        except Exception as e:
            print(f"[ReminderScheduler] Email failed: {e}")

    # Mark as fired
    for r in reminders:
        if r["id"] == reminder_id:
            r["status"] = "fired"
            r["fired_at"] = datetime.now().isoformat()
    _save_reminders(reminders)


def _reschedule_persisted():
    """Re-register pending reminders from file on app startup"""
    reminders = _load_reminders()
    now = datetime.now()
    scheduler = _scheduler

    rescheduled = 0
    for r in reminders:
        if r.get("status") == "pending" and r.get("fire_at"):
            try:
                fire_dt = datetime.fromisoformat(r["fire_at"])
                if fire_dt > now:
                    scheduler.add_job(
                        _fire_reminder,
                        trigger=DateTrigger(run_date=fire_dt),
                        args=[r["id"]],
                        id=r["id"],
                        replace_existing=True,
                    )
                    rescheduled += 1
            except Exception as e:
                print(f"[ReminderScheduler] Could not reschedule {r['id']}: {e}")

    if rescheduled:
        print(f"[ReminderScheduler] Rescheduled {rescheduled} pending reminder(s) from storage.")


# ── Public functions ──────────────────────────────────────────────────────────

def add_reminder(
    title: str,
    fire_at: str,
    note: str = "",
    email: Optional[str] = None,
    recurrence: Optional[str] = None,
) -> dict:
    """
    Schedule a reminder to fire at a specific datetime.

    Args:
        title:      Short title for the reminder
        fire_at:    When to fire — ISO format 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DDTHH:MM'
        note:       Optional longer description or message
        email:      Optional email address to send the reminder to
        recurrence: Optional cron expression for repeating reminders e.g. '0 9 * * 1' (every Monday 9am)

    Returns:
        dict with reminder id, scheduled time, and status
    """
    # Parse fire_at
    try:
        fire_dt = datetime.fromisoformat(fire_at.replace(" ", "T"))
    except ValueError:
        return {"error": f"Invalid date format: '{fire_at}'. Use YYYY-MM-DD HH:MM"}

    if fire_dt <= datetime.now() and not recurrence:
        return {"error": f"Scheduled time {fire_at} is in the past."}

    reminders = _load_reminders()
    reminder_id = _next_id(reminders)

    reminder = {
        "id": reminder_id,
        "title": title,
        "note": note,
        "fire_at": fire_dt.isoformat(),
        "email": email,
        "recurrence": recurrence,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    reminders.append(reminder)
    _save_reminders(reminders)

    # Register with scheduler
    scheduler = get_scheduler()
    try:
        if recurrence:
            trigger = CronTrigger.from_crontab(recurrence)
        else:
            trigger = DateTrigger(run_date=fire_dt)

        scheduler.add_job(
            _fire_reminder,
            trigger=trigger,
            args=[reminder_id],
            id=reminder_id,
            replace_existing=True,
        )
    except Exception as e:
        return {"error": f"Scheduler registration failed: {e}"}

    delivery = f"email to {email}" if email else "console log"
    return {
        "id": reminder_id,
        "title": title,
        "fire_at": fire_dt.isoformat(),
        "recurrence": recurrence or "none (one-time)",
        "delivery": delivery,
        "status": "scheduled",
        "message": f"Reminder '{title}' scheduled for {fire_at}. Delivery: {delivery}",
    }


def list_reminders(status: Optional[str] = None) -> dict:
    """
    List all reminders, optionally filtered by status.

    Args:
        status: Optional filter — 'pending', 'fired', or None for all

    Returns:
        dict with list of reminders and count
    """
    reminders = _load_reminders()

    if status:
        reminders = [r for r in reminders if r.get("status") == status]

    if not reminders:
        label = f"No {status} reminders found." if status else "No reminders found."
        return {"reminders": [], "count": 0, "message": label}

    # Sort by fire_at
    reminders.sort(key=lambda r: r.get("fire_at", ""))

    lines = []
    for r in reminders:
        icon = "✅" if r["status"] == "fired" else "⏳"
        lines.append(
            f"{icon} [{r['id']}] {r['title']} — {r['fire_at']}"
            + (f" | email: {r['email']}" if r.get("email") else "")
            + (f" | note: {r['note']}" if r.get("note") else "")
        )

    return {
        "reminders": reminders,
        "count": len(reminders),
        "summary": "\n".join(lines),
    }


def cancel_reminder(reminder_id: str) -> dict:
    """
    Cancel a pending reminder by ID.

    Args:
        reminder_id: The reminder ID (e.g. 'reminder_1')

    Returns:
        dict with success status and message
    """
    reminders = _load_reminders()
    target = next((r for r in reminders if r["id"] == reminder_id), None)

    if not target:
        return {"success": False, "message": f"Reminder '{reminder_id}' not found."}

    if target["status"] == "fired":
        return {"success": False, "message": f"Reminder '{reminder_id}' already fired."}

    # Remove from scheduler
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(reminder_id)
    except Exception:
        pass  # Job may not exist if app restarted

    # Mark cancelled in file
    for r in reminders:
        if r["id"] == reminder_id:
            r["status"] = "cancelled"
            r["cancelled_at"] = datetime.now().isoformat()

    _save_reminders(reminders)
    return {
        "success": True,
        "message": f"Reminder '{target['title']}' ({reminder_id}) cancelled.",
    }


# ── Claude tool schemas ────────────────────────────────────────────────────────

ADD_REMINDER_SCHEMA = {
    "name": "add_reminder",
    "description": (
        "Schedule a reminder to fire at a specific date and time. "
        "Can deliver via email or console log. Supports one-time and recurring (cron) reminders. "
        "Use when the user says 'remind me', 'set a reminder', 'alert me at', or 'don't let me forget'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short reminder title"},
            "fire_at": {
                "type": "string",
                "description": "When to fire the reminder in YYYY-MM-DD HH:MM format",
            },
            "note": {
                "type": "string",
                "description": "Optional longer description or message body",
                "default": "",
            },
            "email": {
                "type": "string",
                "description": "Optional email address to send the reminder to",
            },
            "recurrence": {
                "type": "string",
                "description": "Optional cron expression for repeating reminders e.g. '0 9 * * 1' for every Monday at 9am",
            },
        },
        "required": ["title", "fire_at"],
    },
}

LIST_REMINDERS_SCHEMA = {
    "name": "list_reminders",
    "description": "List all scheduled reminders. Optionally filter by status: 'pending' or 'fired'.",
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "fired", "cancelled"],
                "description": "Optional filter by reminder status",
            },
        },
        "required": [],
    },
}

CANCEL_REMINDER_SCHEMA = {
    "name": "cancel_reminder",
    "description": "Cancel a pending reminder by its ID.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reminder_id": {
                "type": "string",
                "description": "The reminder ID to cancel (e.g. 'reminder_1')",
            },
        },
        "required": ["reminder_id"],
    },
}

ALL_REMINDER_SCHEMAS = [
    ADD_REMINDER_SCHEMA,
    LIST_REMINDERS_SCHEMA,
    CANCEL_REMINDER_SCHEMA,
]