"""Template for private monitor settings - copy to clinic_monitor_config.py.

clinic_monitor_config.py is gitignored so the ntfy topic never reaches GitHub.
"""

URL = "http://localhost:8080/clinic/"   # page the probe requests
TIMEOUT = 15                            # seconds to wait for a response
REMIND_HOURS = 1                        # re-nag interval while still down
PROBE_MINUTES = 3                       # probe cadence; re-run install_task.ps1 after changing

# Phone push via ntfy.sh ('' = push off). Pick a long random topic name and
# subscribe to it in the ntfy app (Android/iOS). Keep it secret - anyone who
# knows the topic can send and read these notifications.
NTFY_TOPIC = ""
