import re

import requests

_ESCAPE_MAP = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def _esc(s: str) -> str:
    s = s or ""
    for char, repl in _ESCAPE_MAP:
        s = s.replace(char, repl)
    return s


def _section(text: str, header: str) -> str:
    pattern = (
        r"(?:^|\n)" + re.escape(header).replace(r"\ ", r"\s+")
        + r"\s*\n([\s\S]*?)(?=\n[A-Z][A-Z ]{2,}\s*\n|$)"
    )
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _build_experience(text: str) -> str:
    if not text:
        return r"\cvitem{}{}"
    lines = text.split("\n")
    blocks, current = [], []
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue
        if "|" in trimmed and not trimmed.startswith("-") and current:
            blocks.append(current)
            current = []
        current.append(trimmed)
    if current:
        blocks.append(current)

    out = ""
    for block in blocks:
        co_loc = (block[0].split("|") + [""])[:2] if len(block) > 0 else ["", ""]
        title_dates = (block[1].split("|") + [""])[:2] if len(block) > 1 else ["", ""]
        co, loc = [p.strip() for p in co_loc]
        title, dates = [p.strip() for p in title_dates]
        bullets = [l for l in block[2:] if l.startswith("- ")]

        out += f"\n\\cventry{{{_esc(dates)}}}{{{_esc(title)}}}{{{_esc(co)}}}{{{_esc(loc)}}}{{}}{{\n"
        if bullets:
            out += "  \\begin{itemize}\n"
            for b in bullets:
                out += f"    \\item {_esc(b[2:])}\n"
            out += "  \\end{itemize}\n"
        out += "}\n"
    return out or r"\cvitem{}{}"


def _build_education(text: str) -> str:
    if not text:
        return r"\cvitem{}{}"
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("-")]
    out = ""
    for i in range(0, len(lines) - 1, 2):
        school, loc = ([p.strip() for p in lines[i].split("|")] + [""])[:2]
        degree, dates = ([p.strip() for p in lines[i + 1].split("|")] + [""])[:2]
        out += f"\\cventry{{{_esc(dates)}}}{{{_esc(degree)}}}{{{_esc(school)}}}{{{_esc(loc)}}}{{}}{{}}\n"
    return out or r"\cvitem{}{}"


def _build_skills(text: str) -> str:
    if not text:
        return r"\cvitem{}{}"
    lines_out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        clean = re.sub(r"^-\s*", "", line)
        if ":" in clean:
            label, value = clean.split(":", 1)
            lines_out.append(f"\\cvitem{{{_esc(label.strip())}}}{{{_esc(value.strip())}}}")
        else:
            lines_out.append(f"\\cvitem{{}}{{{_esc(clean)}}}")
    return "\n".join(lines_out) or r"\cvitem{}{}"


def build_latex(tailored_output: str) -> str:
    raw = (tailored_output or "").strip()

    name_raw = _section(raw, "NAME")
    contact_raw = _section(raw, "CONTACT")
    summary_raw = _section(raw, "SUMMARY")
    experience_raw = _section(raw, "PROFESSIONAL EXPERIENCE")
    education_raw = _section(raw, "EDUCATION")
    skills_raw = _section(raw, "SKILLS")

    full_name = (name_raw.split("\n")[0] or "Your Name").strip()
    parts = full_name.split(" ")
    first_name = _esc(" ".join(parts[:-1]) if len(parts) > 1 else full_name)
    last_name = _esc(parts[-1] if len(parts) > 1 else "")

    contact_tokens = [
        p.strip() for p in contact_raw.replace("\n", " | ").split("|") if p.strip()
    ]
    email = _esc(next((p for p in contact_tokens if "@" in p), ""))
    phone = _esc(next((p for p in contact_tokens if re.search(r"\d{3}[-.\s]\d{3}", p)), ""))
    linkedin_raw = next((p for p in contact_tokens if re.search(r"linkedin", p, re.IGNORECASE)), "")
    linkedin = _esc(
        re.sub(r"/+$", "", re.sub(r"^linkedin\.com/in/", "", re.sub(r"^https?://(www\.)?", "", linkedin_raw, flags=re.IGNORECASE), flags=re.IGNORECASE))
    )
    city = _esc(
        next(
            (p for p in contact_tokens if "@" not in p and not re.search(r"\d{3}[-.\s]\d{3}", p) and not re.search(r"linkedin", p, re.IGNORECASE)),
            "",
        )
    )

    summary_text = _esc(summary_raw.replace("\n", " ").strip())

    return f"""\\documentclass[11pt,a4paper,sans]{{moderncv}}
\\moderncvstyle{{banking}}
\\moderncvcolor{{blue}}
\\usepackage[scale=0.88]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{hyperref}}
\\nopagenumbers{{}}

\\name{{{first_name}}}{{{last_name}}}
\\phone[mobile]{{{phone}}}
\\email{{{email}}}
\\social[linkedin]{{{linkedin}}}
\\address{{{city}}}{{}}{{}}

\\begin{{document}}
\\makecvtitle

\\section{{Summary}}
\\cvitem{{}}{{{summary_text}}}

\\section{{Professional Experience}}
{_build_experience(experience_raw)}
\\section{{Education}}
{_build_education(education_raw)}

\\section{{Skills}}
{_build_skills(skills_raw)}

\\end{{document}}
"""


def compile_pdf(latex_source: str) -> bytes:
    """Same external compile service the n8n workflow used.
    This is a single point of failure either way — worth knowing, not something
    the n8n-vs-code choice changes.
    """
    resp = requests.post(
        "https://latex.ytotech.com/builds/sync",
        json={"compiler": "lualatex", "resources": [{"main": True, "content": latex_source}]},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.content
