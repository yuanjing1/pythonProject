"""Alert when any of your Teslas starts driving.

Setup (one time):
    pip install teslapy
    python tesla_alert.py
  First run asks for a Tesla refresh token (use 'Tesla Tokens' on Android or
  'Auth app for Tesla' on iOS) or a login callback URL. The token is then
  cached in cache.json - keep that file private.

Settings live in tesla_config.py (gitignored) - copy tesla_config.example.py
to tesla_config.py and fill in your Tesla email, optional Gmail app password
for email alerts, and optional ntfy.sh topic for phone push.

How it works:
  - Polls the vehicle list every POLL_SLEEPING seconds. This does NOT wake
    cars, so sleeping cars keep sleeping (no battery drain).
  - When a car is online, checks its shift state every POLL_ONLINE seconds.
  - Fires one alert per driving session (shift state D/R/N or speed > 0),
    and re-arms once the car is parked or asleep again.
  - Activity is appended to tesla_alert.log (useful when auto-started
    in the background with no console window).
"""

import smtplib
import subprocess
import time
import winsound
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import requests
import teslapy

try:
    from tesla_config import (TESLA_EMAIL, EMAIL_FROM, EMAIL_APP_PASSWORD,
                              EMAIL_TO, NTFY_TOPIC)
except ImportError:
    raise SystemExit("tesla_config.py not found - copy tesla_config.example.py "
                     "to tesla_config.py and fill in your settings.")

BASE_DIR = Path(__file__).resolve().parent

POLL_SLEEPING = 60    # seconds between checks while a car is asleep/offline
POLL_ONLINE = 20      # seconds between checks while a car is awake
DRIVING_STATES = {"D", "R", "N"}

CACHE_FILE = BASE_DIR / "cache.json"        # Tesla auth token cache
LOG_FILE = BASE_DIR / "tesla_alert.log"


def log(msg: str) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line)  # no-op when running under pythonw (no console)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass

""" 
def send_email(subject: str, body: str) -> None:
    if not EMAIL_APP_PASSWORD:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
 """

def send_push(title: str, message: str, link: str = "") -> None:
    """Phone notification via ntfy.sh - needs the ntfy app subscribed to NTFY_TOPIC."""
    if not NTFY_TOPIC:
        return
    headers = {"Title": title, "Priority": "high", "Tags": "car"}
    if link:
        headers["Click"] = link  # tapping the notification opens the map
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}",
                  data=message.encode("utf-8"),
                  headers=headers,
                  timeout=30)


def notify(title: str, message: str, link: str = "") -> None:
    """Phone push + Windows toast + beep on every alert."""
    message = describe_place(message, link)
    log(f"*** {title}: {message} {link}")
    try:
        send_push(title, message, link)
    except Exception as e:
        log(f"push failed: {e}")
    # email disabled for now - uncomment to re-enable
    # try:
    #     send_email(title, message)
    # except Exception as e:
    #     log(f"email failed: {e}")
    try:
        winsound.Beep(1200, 400)
        winsound.Beep(1600, 600)
    except RuntimeError:
        pass
    # Windows toast via PowerShell (no extra packages needed)
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
        "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        f"$t.GetElementsByTagName('text').Item(0).InnerText = '{title}';"
        f"$t.GetElementsByTagName('text').Item(1).InnerText = '{message}';"
        "$n = [Windows.UI.Notifications.ToastNotification]::new($t);"
        "$n.Tag = 'tesla-alert'; $n.Group = 'tesla-alert';"          # same tag -> new toast replaces old one
        "$n.ExpirationTime = [DateTimeOffset]::Now.AddMinutes(30);"  # auto-clear from notification center
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Tesla Alert').Show($n)"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=15,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        pass  # log line + email already happened


def get_address(lat: float, lon: float) -> str:
    """Street address for coordinates via OpenStreetMap (free, no API key).

    Returns '' if the lookup fails - alerts still work, just without a name.
    """
    try:
        r = requests.get("https://nominatim.openstreetmap.org/reverse",
                         params={"lat": lat, "lon": lon, "format": "jsonv2",
                                 "zoom": 18, "addressdetails": 1},
                         headers={"User-Agent": "tesla-alert/1.0"}, timeout=15)
        a = (r.json() or {}).get("address") or {}
        parts = [
            " ".join(p for p in (a.get("house_number"), a.get("road")) if p),
            a.get("city") or a.get("town") or a.get("village") or a.get("suburb"),
            a.get("state"),
        ]
        return ", ".join(p for p in parts if p)
    except Exception:
        return ""


def is_driving(vehicle) -> tuple[bool, str, str]:
    """Return (driving?, detail, maps_link). Only call when vehicle is online."""
    data = vehicle.get_vehicle_data(endpoints="drive_state;location_data")
    drive = data.get("drive_state") or {}
    shift = drive.get("shift_state")
    speed = drive.get("speed") or 0
    lat = drive.get("latitude") or drive.get("native_latitude")
    lon = drive.get("longitude") or drive.get("native_longitude")
    driving = shift in DRIVING_STATES or speed > 0
    detail = f"{shift or 'P'}" # gear=
    maps_link = ""
    if lat is not None and lon is not None:
        # Address lookup happens only when an alert fires (see describe_place),
        # to stay within Nominatim's free-use rate limits.
        detail += f" @ {lat:.5f},{lon:.5f}"
        maps_link = f"https://maps.google.com/?q={lat},{lon}"
    return driving, detail, maps_link


def describe_place(detail: str, maps_link: str) -> str:
    """Swap the raw coordinates in `detail` for a street address, if resolvable."""
    if "?q=" not in maps_link:
        return detail
    try:
        lat, lon = (float(x) for x in maps_link.split("?q=")[1].split(","))
    except ValueError:
        return detail
    address = get_address(lat, lon)
    return detail.split(" @ ")[0] + f" {address}" if address else detail


def main() -> None:
    alerted = {}    # vehicle id -> currently-in-driving-session flag
    last_seen = {}  # vehicle id -> (detail, maps link) from its last reading
    with teslapy.Tesla(TESLA_EMAIL, cache_file=str(CACHE_FILE)) as tesla:
        if not tesla.authorized:
            print("Login needed. Two ways:")
            print(" A) EASIEST: on your phone install 'Tesla Tokens' (Android) or")
            print("    'Auth app for Tesla' (iOS), log in with your Tesla account,")
            print("    and paste the REFRESH token below.")
            print(" B) Or open this URL in an incognito window, log in, and paste")
            print("    the 'Page Not Found' URL (https://auth.tesla.com/void/callback?code=...):\n")
            print(tesla.authorization_url())
            answer = input("\nPaste refresh token or callback URL: ").strip()
            if answer.startswith("http"):
                tesla.fetch_token(authorization_response=answer)
            else:
                tesla.refresh_token(refresh_token=answer)
        log("Logged in. Watching vehicles... (Ctrl+C to stop)")
        for v in tesla.vehicle_list():
            log(f"  - {v['display_name'] or v['vin']}: {v['state']}")
        while True:
            try:
                vehicles = tesla.vehicle_list()  # does not wake sleeping cars
                any_online = False
                for v in vehicles:
                    vid = v["id"]
                    name = v["display_name"] or v["vin"][-6:]
                    state = v["state"]  # online / asleep / offline
                    if state != "online":
                        # Car slept without a parked reading - report last known spot.
                        if alerted.get(vid):
                            d, ln = last_seen.get(vid, ("", ""))
                            notify(f"{name} parked ({state})", d, ln)
                        alerted[vid] = False  # parked & asleep -> re-arm
                        continue
                    any_online = True
                    try:
                        driving, detail, maps_link = is_driving(v)
                    except Exception as e:
                        log(f"{name}: could not read drive state ({e})")
                        continue
                    last_seen[vid] = (detail, maps_link)
                    if driving and not alerted.get(vid):
                        alerted[vid] = True
                        notify(f"{name} ", detail, maps_link)
                    elif not driving:
                        if alerted.get(vid):
                            notify(f"{name} ", detail, maps_link)
                        alerted[vid] = False
                time.sleep(POLL_ONLINE if any_online else POLL_SLEEPING)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                log(f"Error: {e} - retrying in 60s")
                time.sleep(60)


if __name__ == "__main__":
    main()
