import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os

load_dotenv()

# Updated scopes for Google Sheets API v4
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def open_file(creds, ):
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        client = gspread.authorize(creds)
        
        # Store the spreadsheet object
        spreadsheet_url = os.getenv('GOOGLE_SPREADSHEET_LINK')
        if not spreadsheet_url:
            raise ValueError("GOOGLE_SPREADSHEET_LINK environment variable is not set")
        
        spreadsheet = client.open_by_url(spreadsheet_url)
        print(f"Successfully opened spreadsheet: {spreadsheet.title}")
        
        # You can now work with the spreadsheet
        # Example: Get the first worksheet
        worksheet = spreadsheet.sheet1
        print(f"Working with worksheet: {worksheet.title}")
        
    except FileNotFoundError:
        print("Error: credentials.json file not found")
    except ValueError as e:
        print(f"Error: {e}")
    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet not found. Check the URL and permissions.")
    except gspread.exceptions.APIError as e:
        print(f"Google Sheets API Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def write_file():
    print('Is this being written to the google sheets')
