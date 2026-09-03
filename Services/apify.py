import time
from urllib.parse import quote

import requests

import config


def build_linkedin_url(query: str, location: str) -> str:
    return (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={quote(query)}"
        f"&location={quote(location)}"
        "&f_TPR=r86400&f_WT=1%2C2&sortBy=DD"
    )


def start_run(linkedin_url: str, count: int = 10) -> str:
    """Kick off the Apify actor run. Returns the run id."""
    url = f"https://api.apify.com/v2/acts/{config.APIFY_ACTOR_ID}/runs?token={config.APIFY_TOKEN}"
    resp = requests.post(
        url,
        json={"urls": [linkedin_url], "scrapeCompany": False, "count": count},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["data"]["id"]


def wait_for_completion(run_id: str) -> str:
    """Poll every APIFY_POLL_INTERVAL_SECONDS until SUCCEEDED. Returns the dataset id."""
    status_url = (
        f"https://api.apify.com/v2/acts/{config.APIFY_ACTOR_ID}/runs/{run_id}"
        f"?token={config.APIFY_TOKEN}"
    )
    for attempt in range(config.APIFY_MAX_POLL_ATTEMPTS):
        resp = requests.get(status_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data["status"]
        if status == "SUCCEEDED":
            return data["defaultDatasetId"]
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Apify run ended with status {status}")
        time.sleep(config.APIFY_POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"Apify run {run_id} did not finish after "
        f"{config.APIFY_MAX_POLL_ATTEMPTS * config.APIFY_POLL_INTERVAL_SECONDS}s"
    )


def fetch_dataset_items(dataset_id: str) -> list[dict]:
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={config.APIFY_TOKEN}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def scrape_jobs(query: str, location: str, count: int = 10) -> list[dict]:
    linkedin_url = build_linkedin_url(query, location)
    run_id = start_run(linkedin_url, count=count)
    dataset_id = wait_for_completion(run_id)
    return fetch_dataset_items(dataset_id)
