# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from google_sheets import get_google_sheet_data
from google_drive import build_drive_tree
from zipf import generate_zipf_plot
from google_auth import get_google_credentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

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
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        credentials = get_google_credentials(scopes=scopes)
        if credentials:
            # Get the shared drive ID from environment variables
            shared_drive_id = os.environ.get('SHARED_DRIVE_ID')
            if not shared_drive_id:
                flash('SHARED_DRIVE_ID environment variable not set.')
                return render_template('drive_structure.html', drive_tree=drive_tree)

            drive_tree = build_drive_tree(credentials, shared_drive_id)

    except Exception as e:
        print(f"Error building Drive tree: {e}")
        flash('Error fetching Google Drive structure.')

    return render_template('drive_structure.html', drive_tree=drive_tree)

@app.route('/zipf_plot')
def zipf_plot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    generate_zipf_plot()
    return render_template('zipf_plot.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
