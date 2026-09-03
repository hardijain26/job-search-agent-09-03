from datetime import datetime
from html import escape


def build_summary(results: list[dict]) -> tuple[str, str]:
    """results: list of {company, title, postedAt, jobLink, pdfLink}. Returns (subject, html)."""
    today = datetime.now().strftime("%Y-%m-%d")
    rows = ""
    for r in results:
        rows += (
            "<tr>"
            f"<td style='padding:10px;border-bottom:1px solid #eee;font-weight:700;'>{escape(r['company'])}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #eee;'>{escape(r['title'])}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #eee;'>{escape(r['postedAt'])}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #eee;'><a href='{r['jobLink']}'>View Job</a></td>"
            f"<td style='padding:10px;border-bottom:1px solid #eee;'><a href='{r['pdfLink']}'>PDF Resume</a></td>"
            "</tr>"
        )

    body = (
        "<div style='font-family:Arial,sans-serif;font-size:14px;line-height:1.5;color:#222;'>"
        f"<h2>Your ATS resumes are ready ({len(results)})</h2>"
        f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>"
        "<table style='border-collapse:collapse;width:100%;'>"
        "<thead><tr>"
        "<th style='text-align:left;padding:10px;border-bottom:2px solid #ddd;'>Company</th>"
        "<th style='text-align:left;padding:10px;border-bottom:2px solid #ddd;'>Role</th>"
        "<th style='text-align:left;padding:10px;border-bottom:2px solid #ddd;'>Posted</th>"
        "<th style='text-align:left;padding:10px;border-bottom:2px solid #ddd;'>Job</th>"
        "<th style='text-align:left;padding:10px;border-bottom:2px solid #ddd;'>Resume</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f"<p style='color:#aaa;font-size:11px;margin-top:16px;'>ATS Resume Agent — {today}</p>"
        "</div>"
    )
    subject = f"ATS Resumes Ready ({len(results)}) — {today}"
    return subject, body
