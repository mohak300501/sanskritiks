# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_default_secret_key')

# Google Sheets configuration
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
        # Replace with your Google Sheet ID
        sheet_id = os.environ.get('SHEET_ID', 'Your Google Sheet ID') # Set sheet_id env var
        sheet = client.open_by_key(sheet_id).sheet1 # Assuming data is in the first sheet
        data = sheet.get_all_records()
        if data:
            return data[-1] # Get the last row
        else:
            return None
    except Exception as e:
        print(f"Error fetching Google Sheet data: {e}")
        return None

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

if __name__ == '__main__':
    app.run(debug=True)