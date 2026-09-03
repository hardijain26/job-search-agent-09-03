from google.oauth2.credentials import Credentials

import config


def get_credentials() -> Credentials:
    """Build usable Google credentials from the stored refresh token.
    google-auth handles the access-token refresh automatically on first API call.
    """
    return Credentials(
        token=None,
        refresh_token=config.GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        scopes=config.GOOGLE_SCOPES,
    )
