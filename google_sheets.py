import os, json, gspread
from google_auth import get_google_credentials

def get_google_sheet_data():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        credentials = get_google_credentials(scopes=scopes)
        if not credentials:
            return None
        client = gspread.authorize(credentials)
        sheet_id = os.environ.get('SHEET_ID') # Set SHEET_ID env var
        if not sheet_id:
             raise ValueError("SHEET_ID environment variable not set")
        sheet = client.open_by_key(sheet_id).sheet1 # Assuming data is in the first sheet
        data = sheet.get_all_records()
        if data:
            return data[-1] # Get the last row
        else:
            return None
    except Exception as e:
        print(f"Error fetching Google Sheet data: {e}")
        return None
