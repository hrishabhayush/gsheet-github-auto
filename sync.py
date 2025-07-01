import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import pandas as pd
import requests
import hashlib
import re
from io import StringIO
from bs4 import BeautifulSoup

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
        # print(full_table)

        buffer = StringIO(full_table)

        df = pd.read_csv(buffer, sep="|", engine="python", skipinitialspace=True)

        df = df.dropna(axis=1, how="all")

        df = df.iloc[1:].reset_index(drop=True)

        df.columns = [c.strip() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        df['Recruiters'] = ""
        df['Notes'] = ""
        print(df.columns)

        handle_rows(df)
        df["Location"] = df["Location"].apply(clean_html_tags)
        df["Application/Link"] = df["Application/Link"].apply(extract_link_from_html)
        df["unique_key"] = df.apply(generate_key, axis=1)

        new_keys = set(df["unique_key"])
        df.to_csv('data/output.csv', sep=",")
    else:
        raise Exception("Internship table not found.")

def handle_rows(df):
    for i in range(len(df)):
        if df.loc[i, "Company"].strip() == "↳":
            df.loc[i, "Company"] = df.loc[i-1, "Company"]

# Step 6.1: Define function to generate unique key
def generate_key(row):
    return row["Company"].strip() + "|" + row["Role"].strip() + \
    "|" + row["Location"].strip() + "|" + row["Application/Link"] + \
        "|" + row["Date Posted"] + "|" + row["Recruiters"] + "|" + row["Notes"]

def clean_html_tags(text):
    '''
    Clean HTML tags from the location
    '''
    if pd.isna(text):
        return text
    return BeautifulSoup(text, "html.parser").get_text(separator=", ")

def extract_link_from_html(html):
    if pd.isna(html):
        return html
    match = re.search(r'href="([^"]+)"', html)
    return match.group(1) if match else html


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

def normalize(s):
    return re.sub(r'\s+', ' ', s.strip().lower()) if isinstance(s, str) else ''

def generate_key(row):
    return "|".join([
        normalize(row["Company"]),
        normalize(row["Role"]),
        normalize(row["Location"]),
        normalize(row["Application/Link"]),
        normalize(row["Date Posted"]),
        normalize(row["Recruiters"]),
        normalize(row["Notes"]),
    ])

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