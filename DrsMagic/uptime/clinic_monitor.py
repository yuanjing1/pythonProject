"""Periodic uptime probe for the clinic app, with phone push on failure.

One run = one probe, then exit. Windows Task Scheduler drives the cadence
(PROBE_MINUTES in the config) (see install_task.ps1), so the monitor survives reboots and does
not depend on a console window staying open.

Setup (one time):
    copy clinic_monitor_config.example.py -> clinic_monitor_config.py
    fill in NTFY_TOPIC, subscribe to that topic in the ntfy phone app
    powershell -ExecutionPolicy Bypass -File install_task.ps1

Alert policy (avoids a text every probe while the app is down):
  - first failed probe        -> "clinic is DOWN" push
  - still down                -> quiet, re-reminds every REMIND_HOURS
  - first success after down  -> "clinic is back UP" push, with downtime

State lives in clinic_monitor_state.json; activity is appended to
clinic_monitor.log.
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# Config sits next to this file; Task Scheduler's working dir may be elsewhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from clinic_monitor_config import NTFY_TOPIC, URL, TIMEOUT, REMIND_HOURS
except ImportError:
    raise SystemExit("clinic_monitor_config.py not found - copy "
                     "clinic_monitor_config.example.py to it and fill in "
                     "your ntfy topic.")

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "clinic_monitor_state.json"
LOG_FILE = BASE_DIR / "clinic_monitor.log"

RETRY_DELAY = 10   # seconds to wait before the confirming second attempt
TS = "%Y-%m-%d %H:%M:%S"


def log(msg: str) -> None:
    line = f"{datetime.now():{TS}}  {msg}"
    print(line)  # no-op when running under pythonw (no console)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def send_push(title: str, message: str, tags: str, priority: str) -> None:
    """Phone notification via ntfy.sh - needs the ntfy app subscribed to NTFY_TOPIC."""
    if not NTFY_TOPIC:
        log("NTFY_TOPIC is empty - push skipped")
        return
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}",
                  data=message.encode("utf-8"),
                  headers={"Title": title, "Priority": priority,
                           "Tags": tags, "Click": URL},
                  timeout=30)


def notify(title: str, message: str, tags: str, priority: str = "high") -> None:
    log(f"*** {title}: {message}")
    try:
        send_push(title, message, tags, priority)
    except Exception as e:
        log(f"push failed: {e}")


def describe(e: Exception) -> str:
    """Short, phone-readable reason - the raw urllib3 text is a wall of noise."""
    text = str(e).lower()
    if isinstance(e, requests.Timeout) or "timed out" in text:
        return f"no response within {TIMEOUT}s (app hung?)"
    if "refused" in text:
        return "connection refused (app not running)"
    if "getaddrinfo" in text or "name or service" in text:
        return "host not resolvable"
    if isinstance(e, requests.ConnectionError):
        return "connection failed"
    return f"{type(e).__name__}: {str(e).splitlines()[0][:100]}"


def probe() -> tuple[bool, str]:
    """Return (up?, detail). A 5xx or a connection error counts as down."""
    try:
        r = requests.get(URL, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        return False, describe(e)
    if r.status_code >= 500:
        return False, f"HTTP {r.status_code} error page"
    return True, f"HTTP {r.status_code}"


def probe_twice() -> tuple[bool, str]:
    """Confirm a failure with a second attempt, so one blip is not an alert."""
    up, detail = probe()
    if up:
        return up, detail
    log(f"first attempt failed ({detail}) - retrying in {RETRY_DELAY}s")
    time.sleep(RETRY_DELAY)
    return probe()


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as e:
        log(f"could not write state: {e}")


def human(delta: timedelta) -> str:
    mins = int(delta.total_seconds() // 60)
    h, m = divmod(mins, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def main() -> None:
    state = load_state()
    was_down = state.get("down", False)
    now = datetime.now()

    up, detail = probe_twice()

    if up:
        if was_down:
            since = state.get("down_since")
            outage = ""
            if since:
                try:
                    outage = f" after {human(now - datetime.strptime(since, TS))}"
                except ValueError:
                    pass
            notify("clinic is back UP",
                   f"{URL} responded {detail}{outage}", "white_check_mark")
        else:
            log(f"up ({detail})")
        save_state({"down": False, "last_ok": f"{now:{TS}}"})
        return

    if not was_down:
        notify("clinic is DOWN", f"{URL} - {detail}", "rotating_light", "urgent")
        save_state({"down": True, "down_since": f"{now:{TS}}",
                    "last_alert": f"{now:{TS}}", "detail": detail})
        return

    # Still down: stay quiet unless it is time for a reminder.
    last_alert = state.get("last_alert")
    due = True
    if last_alert:
        try:
            due = now - datetime.strptime(last_alert, TS) >= timedelta(hours=REMIND_HOURS)
        except ValueError:
            pass
    if due:
        since = state.get("down_since", "?")
        notify("clinic still DOWN",
               f"{URL} - {detail} (down since {since})", "rotating_light", "urgent")
        state["last_alert"] = f"{now:{TS}}"
    else:
        log(f"still down ({detail}) - reminder not due yet")
    state["detail"] = detail
    save_state(state)


if __name__ == "__main__":
    main()
