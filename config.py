# Application Global Configuration File


# ------------------ imports -------------------------------------------------------------------------------------------


from os import getenv
from pathlib import Path
from dotenv import load_dotenv


# ------------------ settings ------------------------------------------------------------------------------------------


# load environment variables into global environment
load_dotenv()

# flask server settings
FLASK_SECRET_KEY = getenv("FLASK_SECRET_KEY", "abcdefghijklmnopqrstuvwxyz")
DEBUG_HOST = "0.0.0.0"
DEBUG_PORT = 8080

# database settings
DATABASE_FILE = Path("app.db")
ADMIN_PASSWORD = getenv("ADMIN_PASSWORD", "bike")
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

# email service settings
SMTP_KEY = getenv("SMTP_KEY", None)
SENDER = getenv("SENDER", None)
RECIPIENT = getenv("RECIPIENT", None)

# auditor service settings
WED_CLOSE = 16
THU_CLOSE = 20
SAT_CLOSE = 14
FALLBACK = 22