import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# Google Sheets API scopes
GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# GitHub source URL
GITHUB_README_URL = "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/main/README.md"

def get_google_credentials():
    """Load Google Service Account credentials"""
    try:
        return Credentials.from_service_account_file("credentials.json", scopes=GOOGLE_SHEETS_SCOPES)
    except FileNotFoundError:
        raise FileNotFoundError("credentials.json not found")

def get_spreadsheet_url():
    """Get Google Spreadsheet URL from environment"""
    spreadsheet_url = os.getenv('GOOGLE_SPREADSHEET_LINK')
    if not spreadsheet_url:
        raise ValueError("GOOGLE_SPREADSHEET_LINK environment variable is not set")
    return spreadsheet_url 