# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_default_secret_key')

# Google Sheets and Drive configuration
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
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
        sheet_name = os.environ.get('SHEET_NAME', 'Your Google Sheet Name')
        sheet = client.open(sheet_name).sheet1
        data = sheet.get_all_records()
        if data:
            return data[-1]
        else:
            return None
    except Exception as e:
        print(f"Error fetching Google Sheet data: {e}")
        return None

def get_drive_folders(parent_id=None):
    try:
        credentials = get_google_credentials()
        if not credentials:
            return None

        drive_service = build('drive', 'v3', credentials=credentials)

        query = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        else:
            # List root folders in shared drives the service account has access to
            query += " and 'sharedWithMe' in owners"

        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, parents)').execute()
        items = results.get('files', [])
        return items
    except Exception as e:
        print(f"Error fetching Google Drive folders: {e}")
        return None

def build_drive_tree(folders):
    # This is a simplified approach. For a true hierarchical view,
    # you'd need to recursively fetch subfolders for each folder.
    # This function will just list top-level folders for now.
    tree = {}
    if folders:
        for folder in folders:
            tree[folder['id']] = {'name': folder['name'], 'children': []}
    return tree

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == os.environ.get('APP_PASSWORD'):
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    sheet_data = get_google_sheet_data()
    if sheet_data is None:
        flash('Error fetching data from Google Sheet.')
    return render_template('dashboard.html', sheet_data=sheet_data)

@app.route('/drive_structure')
def drive_structure():
    folders = get_drive_folders()
    drive_tree = build_drive_tree(folders)
    if folders is None:
         flash('Error fetching Google Drive structure.')
    return render_template('drive_structure.html', drive_tree=drive_tree)

if __name__ == '__main__':
    app.run(debug=True)