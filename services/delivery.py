import base64
from email.mime.text import MIMEText

import googleapiclient.http
from googleapiclient.discovery import build

import config


def upload_pdf_to_drive(creds, filename: str, pdf_bytes: bytes) -> str:
    """Upload the PDF and return its file id."""
    service = build("drive", "v3", credentials=creds)
    media = googleapiclient.http.MediaInMemoryUpload(pdf_bytes, mimetype="application/pdf")
    file = (
        service.files()
        .create(
            body={"name": filename, "parents": [config.DRIVE_UPLOAD_FOLDER_ID]},
            media_body=media,
            fields="id",
        )
        .execute()
    )
    return file["id"]


def share_file_public(creds, file_id: str) -> None:
    service = build("drive", "v3", credentials=creds)
    service.permissions().create(
        fileId=file_id, body={"role": "reader", "type": "anyone"}
    ).execute()


def send_email(creds, to: str, subject: str, html_body: str) -> None:
    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(html_body, "html")
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
