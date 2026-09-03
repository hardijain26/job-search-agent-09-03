"""
Run this ONCE, locally, on your own machine. It opens a browser, you log in
with your personal Google account and approve access, and it prints a
refresh token. That refresh token (plus your client id/secret) is what lets
the script run unattended in GitHub Actions with no browser involved.

Prerequisites:
1. Go to console.cloud.google.com -> create a project (any name).
2. Enable these APIs: Google Drive API, Google Docs API, Gmail API.
3. Create credentials -> OAuth client ID -> Application type: Desktop app.
4. Download the JSON, save it next to this file as client_secret.json.

Then run:
    pip install google-auth-oauthlib
    python setup_google_oauth.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n--- Save these as GitHub Actions repo secrets ---")
    print(f"GOOGLE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print("---------------------------------------------------")
    print("\nNote: if GOOGLE_REFRESH_TOKEN is blank, you've authorized this app")
    print("before and Google didn't reissue one. Go to")
    print("https://myaccount.google.com/permissions, remove access for this app,")
    print("and run this script again.")


if __name__ == "__main__":
    main()
