import os, json
from google.oauth2.service_account import Credentials

def get_google_credentials(scopes):
    try:
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS environment variable not set")
        credentials_info = json.loads(credentials_json)
        credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return credentials
    except Exception as e:
        print(f"Error loading Google credentials: {e}")
        return None
