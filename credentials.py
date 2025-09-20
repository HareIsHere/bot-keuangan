import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_gsheet_client():
    # Ambil JSON dari env
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("⚠️ GOOGLE_CREDENTIALS tidak ditemukan di environment!")

    google_creds = json.loads(creds_json)

    # Scope Google Sheets
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(google_creds, scopes=scope)
    client = gspread.authorize(creds)
    return client
