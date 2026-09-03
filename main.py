"""
Daily job-search agent. Equivalent to the n8n workflow, run as a single
scheduled script instead of a node graph.

Flow per run:
  1. Pull resume text from Google Docs
  2. Scrape LinkedIn via Apify for the configured query/location
  3. Filter to recent, substantial postings; drop ones already processed
  4. For each new job: tailor resume with Gemini -> build LaTeX -> compile PDF
     -> upload to Drive -> share -> record in Supabase (only on full success)
  5. Email a summary of everything produced this run
"""
import logging
import sys

import config
from services import apify, delivery, job_parser, resume, summary_email, supabase, tailor
from services.google_auth import get_credentials
from services.latex_resume import build_latex, compile_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("job-search-agent")


def process_job(creds, resume_text: str, job: dict) -> dict | None:
    """Returns a result dict for the summary email, or None if this job failed."""
    try:
        tailored = tailor.tailor_resume(resume_text, job["jobDescription"])
        latex_source = build_latex(tailored)
        pdf_bytes = compile_pdf(latex_source)

        safe_title = "".join(c for c in job["title"] if c not in '/\\:*?"<>|')[:80]
        filename = f"{safe_title} - {job['postedAt']}.pdf"

        file_id = delivery.upload_pdf_to_drive(creds, filename, pdf_bytes)
        delivery.share_file_public(creds, file_id)
        pdf_link = f"https://drive.google.com/file/d/{file_id}/view"

        # Only mark as processed once the whole pipeline actually succeeded —
        # unlike the n8n version, a failed PDF build here won't silently
        # blacklist the job from future runs.
        supabase.store_job_record(job)

        log.info("Done: %s @ %s", job["title"], job["company"])
        return {
            "company": job["company"],
            "title": job["title"],
            "postedAt": job["postedAt"],
            "jobLink": job["jobLink"],
            "pdfLink": pdf_link,
        }
    except Exception:
        log.exception("Failed on job: %s @ %s — skipping, will retry next run", job.get("title"), job.get("company"))
        return None


def main() -> int:
    creds = get_credentials()

    log.info("Fetching resume from Google Docs (%s)", config.RESUME_DOC_ID)
    resume_text = resume.get_resume_text(creds, config.RESUME_DOC_ID)
    if not resume_text.strip():
        log.error("Resume text came back empty — aborting run.")
        return 1

    log.info("Scraping LinkedIn: '%s' in '%s'", config.JOB_SEARCH_QUERY, config.JOB_LOCATION)
    raw_items = apify.scrape_jobs(config.JOB_SEARCH_QUERY, config.JOB_LOCATION)
    log.info("Apify returned %d raw items", len(raw_items))

    jobs = job_parser.parse_and_filter(raw_items)
    log.info("%d jobs passed recency/quality filters", len(jobs))

    new_jobs = supabase.filter_new_jobs(jobs)
    log.info("%d are new (not already processed)", len(new_jobs))

    if not new_jobs:
        log.info("Nothing new to process today. Exiting without sending an email.")
        return 0

    results = []
    for job in new_jobs:
        result = process_job(creds, resume_text, job)
        if result:
            results.append(result)

    if not results:
        log.warning("All %d job(s) failed to process — sending no email, check logs above.", len(new_jobs))
        return 1

    subject, html = summary_email.build_summary(results)
    delivery.send_email(creds, config.USER_EMAIL, subject, html)
    log.info("Sent summary email for %d resume(s).", len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
