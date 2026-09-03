import re
from datetime import datetime, timedelta, timezone

import config

_TAG_BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAG_BLOCK = re.compile(r"</?(li|p|div|h[1-6])[^>]*>", re.IGNORECASE)
_TAG_ANY = re.compile(r"<[^>]+>")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = _TAG_BREAK.sub("\n", html)
    text = _TAG_BLOCK.sub("\n", text)
    text = _TAG_ANY.sub("", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
    )
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def parse_and_filter(raw_items: list[dict]) -> list[dict]:
    """Mirrors the n8n 'Parse Apify Job Results' code node: dedupe by link,
    drop postings older than DAYS_LOOKBACK, drop thin descriptions.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=config.DAYS_LOOKBACK)).date().isoformat()
    seen = set()
    jobs = []

    for item in raw_items:
        job_link = item.get("link") or item.get("jobUrl") or item.get("url") or ""
        if not job_link or job_link in seen:
            continue

        posted_at = item.get("postedAt") or ""
        if posted_at and posted_at < cutoff:
            continue

        description_html = item.get("descriptionHtml")
        job_description = _strip_html(description_html) if description_html else (item.get("descriptionText") or "")
        if not job_description or len(job_description) < 50:
            continue

        jobs.append(
            {
                "title": item.get("title") or "No Title",
                "company": item.get("companyName") or "Unknown Company",
                "location": item.get("location") or "Unknown Location",
                "postedAt": posted_at,
                "employmentType": item.get("employmentType") or "",
                "seniorityLevel": item.get("seniorityLevel") or "",
                "jobLink": job_link,
                "jobDescription": job_description,
            }
        )
        seen.add(job_link)
        if len(jobs) >= 20:
            break

    return jobs[: config.MAX_JOBS_PER_RUN]
