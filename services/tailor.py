import time
import requests
import logging

import config

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = """You are an expert ATS resume optimizer.

Your task is to revise the resume so it is optimized for Applicant Tracking Systems (ATS) and tailored to the target job (JD).

Keyword Optimization: Extract the most important hard skills, technical terms, tools, certifications, and role-specific keywords from the JD. Naturally integrate these throughout the resume — es[...]

Role Alignment: Identify responsibilities and achievements from the current resume that most closely match the target role. Rewrite bullet points to highlight quantifiable achievements, results, a[...]

Professional Voice: Use strong action verbs (Led, Launched, Optimized, Delivered, Drove, Built, Reduced, Increased). Focus on measurable outcomes where they exist in the original. Do NOT invent me[...]

Bullet rules: Each bullet = action + what + outcome. Max 4-6 bullets per role. Max 2 pages total content.

Final Output (STRICT — follow exactly):
Return ONLY plain text. No Markdown. No asterisks. No ### headers. No horizontal rules. No bullet symbols like •.

Use ONLY these section headers (ALL CAPS, on their own line):
NAME
CONTACT
SUMMARY
PROFESSIONAL EXPERIENCE
EDUCATION
SKILLS

Separate sections with one blank line.
For bullets use: - (hyphen + space)
For job entries use exactly:
COMPANY | LOCATION
TITLE | DATES
- bullet
- bullet

Do not invent facts, companies, dates, or metrics."""


def tailor_resume(resume_text: str, job_description: str) -> str:
    """Tailor resume to job description with exponential backoff retry logic."""
    user_message = (
        "I am providing two artifacts:\n\n"
        f"My current resume:\n{resume_text}\n\n"
        "A target job description (JD) for the role I am applying to:\n"
        f"{job_description}"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_MESSAGE}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
    }
    
    last_error = None
    for attempt in range(4):  # 4 attempts: initial + 3 retries
        try:
            logger.debug(f"Tailor attempt {attempt + 1}/4 for Gemini API")
            resp = requests.post(url, json=body, timeout=120)
            
            if resp.ok:
                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    raise RuntimeError(f"Gemini returned no candidates: {data}")
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts).strip()

            last_error = f"Gemini API error {resp.status_code}: {resp.text}"
            
            # Retry on rate limit (429) and server errors (503, 504)
            if resp.status_code in (429, 503, 504) and attempt < 3:
                wait_time = (2 ** attempt) * 10  # 10s, 20s, 40s exponential backoff
                logger.warning(
                    f"Gemini API returned {resp.status_code}. "
                    f"Retrying in {wait_time}s... (attempt {attempt + 1}/4)"
                )
                time.sleep(wait_time)
                continue
            
            # Don't retry on client errors like 400, 401
            logger.error(f"Gemini API error {resp.status_code}: {resp.text}")
            break
            
        except requests.exceptions.Timeout:
            last_error = "Gemini API request timed out"
            if attempt < 3:
                wait_time = (2 ** attempt) * 10
                logger.warning(
                    f"Request timeout. Retrying in {wait_time}s... (attempt {attempt + 1}/4)"
                )
                time.sleep(wait_time)
                continue
            break
        except requests.exceptions.RequestException as e:
            last_error = f"Request error: {str(e)}"
            if attempt < 3:
                wait_time = (2 ** attempt) * 10
                logger.warning(
                    f"Request failed: {str(e)}. "
                    f"Retrying in {wait_time}s... (attempt {attempt + 1}/4)"
                )
                time.sleep(wait_time)
                continue
            break

    raise RuntimeError(last_error or "Failed to tailor resume after all retries")
