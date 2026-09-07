from urllib.parse import quote

import requests

import config

_HEADERS = {
    "apikey": config.SUPABASE_KEY,
    "Authorization": f"Bearer {config.SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def job_already_seen(job_url: str) -> bool:
    url = (
        f"{config.SUPABASE_URL}/rest/v1/jobs"
        f"?job_url=eq.{quote(job_url, safe='')}&select=job_url"
    )
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return len(resp.json()) > 0
    except requests.RequestException:
        # Fail open: if Supabase is unreachable, treat as "not seen" so we
        # don't silently skip real jobs. Duplicate emails are the safer failure.
        return False


def filter_new_jobs(jobs: list[dict]) -> list[dict]:
    return [job for job in jobs if not job_already_seen(job["jobLink"])]


def store_job_record(job: dict) -> None:
    # Validate configuration early
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY environment variables must be configured. "
            "Check GitHub Actions secrets in repository settings."
        )
    
    url = f"{config.SUPABASE_URL}/rest/v1/jobs"
    
    # Validate URL format
    if not url.startswith("https://"):
        raise ValueError(
            f"Invalid SUPABASE_URL format: {config.SUPABASE_URL}. "
            "Expected format: https://[project-id].supabase.co"
        )
    
    payload = {
        "job_url": job["jobLink"],
        "job_title": job["title"],
        "company": job["company"],
        "processed_at": None,  # let Supabase default / trigger set this, or set client-side below
    }
    from datetime import datetime, timezone
    payload["processed_at"] = datetime.now(timezone.utc).isoformat()

    resp = requests.post(url, headers=_HEADERS, json=payload, timeout=15)
    resp.raise_for_status()
