from googleapiclient.discovery import build


def get_resume_text(creds, doc_id: str) -> str:
    """Pull the resume Google Doc and flatten it to plain text.
    Same logic as the n8n 'Extract Full Text' code node.
    """
    service = build("docs", "v1", credentials=creds)
    doc = service.documents().get(documentId=doc_id).execute()

    full_text = ""
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for pe in paragraph.get("elements", []):
            text_run = pe.get("textRun")
            if text_run:
                full_text += text_run.get("content", "")

    return full_text
