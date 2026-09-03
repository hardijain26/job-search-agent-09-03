"""
Central config. Everything comes from environment variables so the same
code runs locally (.env via python-dotenv) and in GitHub Actions (repo secrets).
"""
import os


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


# --- Google OAuth (personal account, obtained once via setup_google_oauth.py) ---
GOOGLE_CLIENT_ID = _require("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _require("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = _require("GOOGLE_REFRESH_TOKEN")

# --- Resume source ---
RESUME_DOC_ID = _require("RESUME_DOC_ID")  # Google Doc file ID

# --- Job search parameters ---
JOB_SEARCH_QUERY = os.environ.get("JOB_SEARCH_QUERY", "Growth Product Manager")
JOB_LOCATION = os.environ.get("JOB_LOCATION", "Netherlands")
DAYS_LOOKBACK = int(os.environ.get("DAYS_LOOKBACK", "7"))
MAX_JOBS_PER_RUN = int(os.environ.get("MAX_JOBS_PER_RUN", "5"))

# --- Apify (LinkedIn scraper) ---
APIFY_ACTOR_ID = os.environ.get("APIFY_ACTOR_ID", "curious_coder~linkedin-jobs-scraper")
APIFY_TOKEN = _require("APIFY_TOKEN")
APIFY_POLL_INTERVAL_SECONDS = int(os.environ.get("APIFY_POLL_INTERVAL_SECONDS", "10"))
APIFY_MAX_POLL_ATTEMPTS = int(os.environ.get("APIFY_MAX_POLL_ATTEMPTS", "30"))  # 5 min cap

# --- Gemini (resume tailoring) ---
GEMINI_API_KEY = _require("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# --- Supabase (dedup store) ---
SUPABASE_URL = _require("SUPABASE_URL")
SUPABASE_KEY = _require("SUPABASE_KEY")

# --- Delivery ---
USER_EMAIL = _require("USER_EMAIL")
DRIVE_UPLOAD_FOLDER_ID = os.environ.get("DRIVE_UPLOAD_FOLDER_ID", "root")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
