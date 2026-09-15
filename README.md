# Job Search Agent 

Same pipeline as the n8n template: daily LinkedIn scrape → ATS-tailored resume
per job → PDF → Drive → email digest. Runs as a plain Python script on a
GitHub Actions cron, so there's no n8n instance to keep alive and no visual
canvas to debug — just one script and a set of logs.

## One-time setup

### 1. Google OAuth (Drive read/write + Docs read + Gmail send)
1. Go to [console.cloud.google.com](https://console.cloud.google.com), create a project.
2. Enable: **Google Drive API**, **Google Docs API**, **Gmail API**.
3. Credentials → **Create OAuth client ID** → Application type: **Desktop app**. Download the JSON as `client_secret.json`, put it next to `setup_google_oauth.py`.
4. Locally: `pip install google-auth-oauthlib` then `python setup_google_oauth.py`. Log in with your personal Google account, approve access.
5. It prints `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` — save all three as GitHub repo secrets (step 5 below).

This uses your personal Gmail/Drive account directly — no Workspace admin needed, no service account.

### 2. Apify
1. Sign up at [apify.com](https://apify.com), grab your API token from Settings → Integrations.
2. Confirm you have access to the `curious_coder~linkedin-jobs-scraper` actor (or swap in whichever LinkedIn scraper actor you actually use — set `APIFY_ACTOR_ID`).

### 3. Gemini
Get an API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### 4. Supabase (dedup store)
1. Create a project at [supabase.com](https://supabase.com).
2. In the SQL editor, run:
   ```sql
   create table jobs (
     id bigint generated always as identity primary key,
     job_url text unique not null,
     job_title text,
     company text,
     processed_at timestamptz
   );
   ```
3. Grab the project URL and the `anon` (or `service_role`, for write access without RLS fuss) key from Settings → API.

### 5. GitHub repo secrets
Settings → Secrets and variables → Actions → New repository secret. Add:

| Secret | Example |
|---|---|
| `GOOGLE_CLIENT_ID` | from step 1 |
| `GOOGLE_CLIENT_SECRET` | from step 1 |
| `GOOGLE_REFRESH_TOKEN` | from step 1 |
| `RESUME_DOC_ID` | the ID in your resume's Google Doc URL |
| `USER_EMAIL` | where the daily digest goes |
| `JOB_SEARCH_QUERY` | e.g. `Growth Product Manager` |
| `JOB_LOCATION` | e.g. `Netherlands` |
| `APIFY_ACTOR_ID` | actor identifier |
| `APIFY_TOKEN` | from step 2 |
| `GEMINI_API_KEY` | from step 3 |
| `SUPABASE_URL` | from step 4 |
| `SUPABASE_KEY` | from step 4 |
| `DRIVE_UPLOAD_FOLDER_ID` | optional, defaults to Drive root |

Push this repo (private is fine — GitHub Actions on private repos gets 2,000 free minutes/month, this job uses a few minutes/day). The workflow runs automatically at 07:00 UTC, or trigger it manually from the Actions tab any time to test.

## What changed vs. the n8n version (and why)

- **Location and query are configurable**, not hardcoded to San Francisco — set via `JOB_LOCATION`/`JOB_SEARCH_QUERY` secrets.
- **A job is only marked "processed" in Supabase after the PDF is actually built, uploaded, and shared** — not before. In the original, the Supabase write happened before the LaTeX/PDF step, so a failed PDF build would still blacklist that job from ever being retried. Here, a failure just means it's picked up again next run.
- **One job failing doesn't kill the run.** If Gemini or the LaTeX compiler chokes on one job, that one is logged and skipped; the rest still get processed and emailed.
- **Supabase lookups fail open**: if Supabase itself is briefly unreachable, jobs are treated as "not yet seen" rather than silently dropped — you might get an occasional duplicate email, which is a cheaper failure than missing a job entirely.

## Known single points of failure (same in both versions)
- `latex.ytotech.com` is a third-party free compile service with no SLA. If it goes down, resume generation for that run fails. Worth knowing if you want to eventually self-host a LaTeX compiler (e.g. a `pandoc`/`tectonic` Docker step) instead.
- The Apify LinkedIn actor's data shape can change without notice since it's scraping, not an official API — that's a scraping risk independent of n8n vs. code.

## Local testing
```bash
pip install -r requirements.txt
export GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... GOOGLE_REFRESH_TOKEN=...
export RESUME_DOC_ID=... USER_EMAIL=... APIFY_TOKEN=... GEMINI_API_KEY=...
export SUPABASE_URL=... SUPABASE_KEY=...
python main.py
```
