import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

# Updated scopes for Google Sheets API v4
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

'''
Returns the first worksheet and the dataframe with all the records
'''
def open_file(creds, spreadsheet_url):
    try:    
        client = gspread.authorize(creds)    
        # Store the spreadsheet object
        
        spreadsheet = client.open_by_url(spreadsheet_url)
        
        # Get the first worksheet
        worksheet = spreadsheet.sheet1
        dataframe = pd.DataFrame(worksheet.get_all_records())
        return worksheet, dataframe
 
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

'''
This function will have the automation script
'''
def write_file(creds, spreadsheet_url):
    ws, _ = open_file(creds=creds, spreadsheet_url=spreadsheet_url)
    ws.update_acell('B1', 'Bingo!')
    return val

    
def main():
    print("STARTING GOOGLE SHEETS AUTOMATION")
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    spreadsheet_url = os.getenv('GOOGLE_SPREADSHEET_LINK')
    if not spreadsheet_url:
        raise ValueError("GOOGLE_SPREADSHEET_LINK environment variable is not set")
    ws = open_file(creds, spreadsheet_url)
    value = write_file(creds, spreadsheet_url)
    values_list = ws.row_values(1)
    print(values_list)
    print(value)

main()