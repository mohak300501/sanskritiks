import os, re, json, io
import numpy as np
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth import get_google_credentials

def download_drive_file(file_id, credentials):
    try:
        service = build('drive', 'v3', credentials=credentials)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def generate_zipf_plot():
    # --- CONFIGURATION ---
    file_id = os.environ.get('UNIQUE_JSON_ID')
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = get_google_credentials(scopes)
    file_content = download_drive_file(file_id, credentials)
    if file_content is None:
        print("Failed to get file content")
        return
    token_frequency = json.loads(file_content)

    # --- SORT BY FREQUENCY DESC ---
    frequencies = sorted(token_frequency.values(), reverse=True)
    ranks = np.arange(1, len(frequencies) + 1)

    # --- PLOT ZIPF'S LAW GRAPH ---
    s = 1.0                  # Exponent in Zipf's law
    C = frequencies[0]       # Frequency of the most common token

    plt.figure(figsize=(10,6))
    plt.loglog(ranks, frequencies, marker=".", label="Sanskrit tokens")
    plt.title("Zipf's Law: Token Frequency vs Rank (log-log scale)")
    plt.xlabel("Rank of token")
    plt.ylabel("Frequency of token")
    plt.grid(True, which="both", ls="--", lw=0.5)
    ideal = C / ranks ** s
    plt.loglog(ranks, ideal, linestyle="-", color="red", alpha=0.5, label="Ideal ~1/r")
    plt.legend()
    plt.savefig('static/zipf_plot.png')
    plt.close()

if __name__ == "__main__":
    generate_zipf_plot()
