# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Google Sheets and Drive configuration
scopes = [
    'https://www.googleapis.com/auth/spreadsheets.readonly', # Readonly scope for Sheets
    'https://www.googleapis.com/auth/drive.readonly' # Readonly scope for Drive
]

def get_google_credentials():
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

def get_google_sheet_data():
    try:
        credentials = get_google_credentials()
        if not credentials:
            return None
        client = gspread.authorize(credentials)
        # Use open_by_key instead of open
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

def get_drive_items(service, parent_id=None, drive_id=None):
    items = []
    page_token = None
    while True:
        try:
            # Construct the query to search within the shared drive if drive_id is provided
            query = "trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            if drive_id:
                 query += f" and '{drive_id}' in collections"

            response = service.files().list(
                q=query,
                spaces='drive',
                corpora='drive' if drive_id else 'user',
                driveId=drive_id if drive_id else None,
                includeItemsFromAllDrives=True if drive_id else None,
                supportsAllDrives=True if drive_id else None,
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token
            ).execute()
            items.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        except HttpError as error:
            print(f'An error occurred: {error}')
            break
    return items

def build_drive_tree(service, parent_id=None, drive_id=None):
    tree = {}
    items = get_drive_items(service, parent_id, drive_id)
    for item in items:
        item_id = item['id']
        item_name = item['name']
        mime_type = item['mimeType']
        if mime_type == 'application/vnd.google-apps.folder':
            tree[item_id] = {'name': item_name, 'children': build_drive_tree(service, item_id, drive_id)}
        else:
            tree[item_id] = {'name': item_name, 'is_file': True}
    return tree

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == os.environ.get('APP_PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    sheet_data = get_google_sheet_data()
    if sheet_data is None:
        flash('Error fetching data from Google Sheet.')
    return render_template('dashboard.html', sheet_data=sheet_data)

@app.route('/drive_structure')
def drive_structure():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    drive_tree = {}
    try:
        credentials = get_google_credentials()
        if credentials:
            drive_service = build('drive', 'v3', credentials=credentials)
            # Get the shared drive ID from environment variables
            shared_drive_id = os.environ.get('SHARED_DRIVE_ID')
            if not shared_drive_id:
                flash('SHARED_DRIVE_ID environment variable not set.')
                return render_template('drive_structure.html', drive_tree=drive_tree)

            # Fetch the root folder ID of the shared drive
            root_folder = drive_service.files().list(
                q=f"mimeType='application/vnd.google-apps.folder' and name='{drive_service.drives().get(driveId=shared_drive_id).execute()['name']}'",
                corpora='drive',
                driveId=shared_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields='files(id)'
            ).execute().get('files', [])

            if not root_folder:
                 flash(f'Could not find the root folder for shared drive ID {shared_drive_id}.')
                 return render_template('drive_structure.html', drive_tree=drive_tree)
            
            root_folder_id = root_folder[0]['id']

            drive_tree = build_drive_tree(drive_service, parent_id=root_folder_id, drive_id=shared_drive_id)




    except Exception as e:
        print(f"Error building Drive tree: {e}")
        flash('Error fetching Google Drive structure.')

    return render_template('drive_structure.html', drive_tree=drive_tree)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
