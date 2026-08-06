"""Template for private settings - copy to tesla_config.py and fill in.

tesla_config.py is gitignored so your personal values never reach GitHub.
"""

TESLA_EMAIL = "you@example.com"         # your Tesla account email

# Email alerts via Gmail ('' password = email off)
EMAIL_FROM = "you@gmail.com"            # Gmail account that sends the alert
EMAIL_APP_PASSWORD = ""                 # 16-char Gmail app password
EMAIL_TO = "you@gmail.com"              # where to receive alerts

# Phone push via ntfy.sh ('' = phone push off). Pick a long random topic
# name and subscribe to it in the ntfy phone app. Keep it secret - anyone
# who knows it can send/read these notifications.
NTFY_TOPIC = ""
