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
        return None, None
    except ValueError as e:
        print(f"Error: {e}")
        return None, None
    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet not found. Check the URL and permissions.")
        return None, None
    except gspread.exceptions.APIError as e:
        print(f"Google Sheets API Error: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None

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

        buffer = StringIO(full_table)
        df = pd.read_csv(buffer, sep="|", engine="python", skipinitialspace=True)
        df = df.dropna(axis=1, how="all")
        df = df.iloc[1:].reset_index(drop=True)
        df.columns = [c.strip() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Add empty columns for manual tracking
        df['Recruiters'] = ""
        df['Notes'] = ""
        
        print(f"Extracted {len(df)} internships from GitHub")

        handle_rows(df)
        df["Location"] = df["Location"].apply(clean_html_tags)
        df["Application/Link"] = df["Application/Link"].apply(extract_link_from_html)
        df["unique_key"] = df.apply(generate_key, axis=1)

        # Save to local CSV for backup
        df.to_csv('data/output.csv', sep=",", index=False)
        
        return df
    else:
        raise Exception("Internship table not found.")

def handle_rows(df):
    '''
    Handle rows where Company is "↳" (continuation of previous company)
    '''
    for i in range(len(df)):
        if df.loc[i, "Company"].strip() == "↳":
            df.loc[i, "Company"] = df.loc[i-1, "Company"]

def normalize(s):
    '''
    Normalize strings for consistent comparison
    '''
    return re.sub(r'\s+', ' ', s.strip().lower()) if isinstance(s, str) else ''

def generate_key(row):
    '''
    Generate unique key for each internship posting
    '''
    return "|".join([
        normalize(row["Company"]),
        normalize(row["Role"]),
        normalize(row["Location"]),
        normalize(row["Application/Link"]),
        normalize(row["Date Posted"]),
        normalize(row.get("Recruiters", "")),
        normalize(row.get("Notes", "")),
    ])

def clean_html_tags(text):
    '''
    Clean HTML tags from the location
    '''
    if pd.isna(text):
        return text
    return BeautifulSoup(text, "html.parser").get_text(separator=", ")

def extract_link_from_html(html):
    '''
    Extract actual URL from HTML link tags
    '''
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
        print("No changes detected in source data")
        return False

    # Save the new hash 
    with open(hash_path, "w") as f:
        f.write(readme_hash)
    
    print("Changes detected in source data")
    return True

def smart_sync_to_sheets(worksheet, new_df, existing_df):
    '''
    Smart sync that preserves manual notes and only adds new/changed internships
    '''
    print("Starting smart sync to Google Sheets...")
    
    # If existing sheet is empty, upload everything
    if existing_df.empty or len(existing_df) == 0:
        print("Empty sheet detected. Uploading all data...")
        
        # Prepare data for upload (excluding index column)
        upload_data = [new_df.columns.tolist()] + new_df.values.tolist()
        
        # Clear sheet and upload
        worksheet.clear()
        worksheet.update(upload_data)
        print(f"Uploaded {len(new_df)} new internships")
        return

    # Create lookup for existing data using unique keys
    existing_lookup = {}
    if 'unique_key' in existing_df.columns:
        for idx, row in existing_df.iterrows():
            # Generate key based on core fields (excluding manual fields)
            core_key = "|".join([
                normalize(row.get("Company", "")),
                normalize(row.get("Role", "")),
                normalize(row.get("Location", "")),
                normalize(row.get("Application/Link", "")),
                normalize(row.get("Date Posted", "")),
            ])
            existing_lookup[core_key] = {
                'row_idx': idx + 2,  # +2 because sheets are 1-indexed and we have header
                'recruiters': row.get("Recruiters", ""),
                'notes': row.get("Notes", ""),
                'full_key': row.get("unique_key", "")
            }

    # Track changes
    new_internships = []
    updates_needed = []
    
    for idx, new_row in new_df.iterrows():
        # Generate core key (without manual fields)
        core_key = "|".join([
            normalize(new_row["Company"]),
            normalize(new_row["Role"]),
            normalize(new_row["Location"]),
            normalize(new_row["Application/Link"]),
            normalize(new_row["Date Posted"]),
        ])
        
        if core_key in existing_lookup:
            # Internship exists - preserve manual data
            existing_data = existing_lookup[core_key]
            new_row["Recruiters"] = existing_data['recruiters']
            new_row["Notes"] = existing_data['notes']
            
            # Check if core data changed (unlikely but possible)
            new_full_key = generate_key(new_row)
            if new_full_key != existing_data['full_key']:
                updates_needed.append({
                    'row': existing_data['row_idx'],
                    'data': new_row
                })
        else:
            # New internship
            new_internships.append(new_row)
    
    # Apply updates
    if updates_needed:
        print(f"Updating {len(updates_needed)} existing internships...")
        for update in updates_needed:
            row_data = [update['data'][col] for col in new_df.columns]
            worksheet.update(f"A{update['row']}:{chr(65+len(new_df.columns)-1)}{update['row']}", [row_data])
    
    # Add new internships
    if new_internships:
        print(f"Adding {len(new_internships)} new internships...")
        next_row = len(existing_df) + 2  # +2 for header and 1-indexing
        
        for new_internship in new_internships:
            row_data = [new_internship[col] for col in new_df.columns]
            worksheet.update(f"A{next_row}:{chr(65+len(new_df.columns)-1)}{next_row}", [row_data])
            next_row += 1
    
    print(f"Sync complete! Added {len(new_internships)} new, updated {len(updates_needed)} existing internships.")

def main():
    '''
    The main function
    '''
    print("STARTING GOOGLE SHEETS AUTOMATION")
    
    # Load credentials
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    except FileNotFoundError:
        print("Error: credentials.json not found")
        return

    spreadsheet_url = os.getenv('GOOGLE_SPREADSHEET_LINK')
    if not spreadsheet_url:
        raise ValueError("GOOGLE_SPREADSHEET_LINK environment variable is not set")
    
    github_url = "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/main/README.md"

    # Check for changes first
    if not detect_changes(github_url):
        return
    
    # Get existing data from Google Sheets
    worksheet, existing_df = open_file(creds, spreadsheet_url)
    if worksheet is None:
        print("Failed to connect to Google Sheets")
        return
    
    # Extract new data from GitHub
    try:
        new_df = extract_information(github_url)
    except Exception as e:
        print(f"Error extracting data from GitHub: {e}")
        return
    
    # Perform smart sync
    smart_sync_to_sheets(worksheet, new_df, existing_df)

if __name__ == "__main__":
    main()