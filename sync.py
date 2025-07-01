import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import pandas as pd
import requests
import hashlib
import re

load_dotenv()

# Updated scopes for Google Sheets API v4
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def open_file(creds, spreadsheet_url):
    '''
    Returns the first worksheet and the dataframe with all the records
    '''
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

def write_file(creds, spreadsheet_url):
    '''
    This function will have the automation script from the github to write to the google sheets
    '''
    ws, _ = open_file(creds=creds, spreadsheet_url=spreadsheet_url)
    ws.update_acell('B1', 'Bingo!')    

def get_readme(url):
    ''' 
    Fetches the raw README.md of the github repository
    '''
    readme = requests.get(url).text
    return readme


def extract_information(url):
    '''
    Extract the internship Markdown table from the README.md
    '''
    readme_text = get_readme(url)
    pattern = r'\| Company \| Role \| Location \| Application/Link \| Date Posted \|\n\|[-| ]+\|\n((?:\|.*\|\n?)*)'

    match = re.search(pattern, readme_text)

    if match:
        table_body = match.group(1)
        full_table = (
                    "| Company | Role | Location | Application/Link | Date Posted |\n"
        "| ------- | ---- | -------- | ---------------- | ----------- |\n"
        + table_body
        )
        print(full_table)
    else:
        raise Exception("Internship table not found.")


def detect_changes(url):
    '''
    Detect whether the raw README.md has changed or not 
    '''
    readme = get_readme(url)
    readme_hash = hashlib.sha256(readme.encode()).hexdigest()
    hash_path = "last_hash.txt"
    last_hash = ""

    if os.path.exists(hash_path):
        with open(hash_path, "r") as f:
            last_hash = f.read().strip()
    
    if readme_hash == last_hash:
        print("No changes detected")
        exit()

    # Save the new hash 
    with open(hash_path, "w") as f:
        f.write(readme_hash)
    
def main():
    '''
    The main function
    '''
    print("STARTING GOOGLE SHEETS AUTOMATION")
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    spreadsheet_url = os.getenv('GOOGLE_SPREADSHEET_LINK')
    if not spreadsheet_url:
        raise ValueError("GOOGLE_SPREADSHEET_LINK environment variable is not set")
    
    github_url = "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/main/README.md"

    ws = open_file(creds, spreadsheet_url)
    # value = write_file(creds, spreadsheet_url)
    # values_list = ws.row_values(1)
    # readme = get_readme(github_url)
    extract_information(github_url)
    # print(values_list)
    # print(value)

main()