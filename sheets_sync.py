import gspread
import pandas as pd
from github_data import normalize_text, generate_unique_key

def connect_to_sheet(credentials, spreadsheet_url):
    """Connect to Google Sheets and return worksheet and dataframe"""
    try:    
        client = gspread.authorize(credentials)    
        spreadsheet = client.open_by_url(spreadsheet_url)
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

def smart_sync_to_sheets(worksheet, new_df, existing_df):
    """Smart sync that preserves manual notes and only adds new/changed internships"""
    print("Starting smart sync to Google Sheets...")
    
    # Create a copy for Google Sheets without the unique_key column
    sheets_columns = [col for col in new_df.columns if col != 'unique_key']
    new_df_for_sheets = new_df[sheets_columns].copy()
    
    # If existing sheet is empty, upload everything
    if existing_df.empty or len(existing_df) == 0:
        print("Empty sheet detected. Uploading all data...")
        
        # Prepare data for upload (excluding unique_key column)
        upload_data = [new_df_for_sheets.columns.tolist()] + new_df_for_sheets.values.tolist()
        
        # Clear sheet and upload
        worksheet.clear()
        worksheet.update(upload_data)
        print(f"Uploaded {len(new_df_for_sheets)} new internships")
        return

    # Create lookup for existing data using unique keys
    existing_lookup = {}
    if 'unique_key' in existing_df.columns:
        for idx, row in existing_df.iterrows():
            # Generate key based on core fields (excluding manual fields)
            core_key = "|".join([
                normalize_text(row.get("Company", "")),
                normalize_text(row.get("Role", "")),
                normalize_text(row.get("Location", "")),
                normalize_text(row.get("Application/Link", "")),
                normalize_text(row.get("Date Posted", "")),
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
            normalize_text(new_row["Company"]),
            normalize_text(new_row["Role"]),
            normalize_text(new_row["Location"]),
            normalize_text(new_row["Application/Link"]),
            normalize_text(new_row["Date Posted"]),
        ])
        
        if core_key in existing_lookup:
            # Internship exists - preserve manual data
            existing_data = existing_lookup[core_key]
            new_row["Recruiters"] = existing_data['recruiters']
            new_row["Notes"] = existing_data['notes']
            
            # Check if core data changed (unlikely but possible)
            new_full_key = generate_unique_key(new_row)
            if new_full_key != existing_data['full_key']:
                # Prepare row data without unique_key for sheets
                row_for_sheets = new_row[sheets_columns]
                updates_needed.append({
                    'row': existing_data['row_idx'],
                    'data': row_for_sheets
                })
        else:
            # New internship - prepare for sheets without unique_key
            new_row_for_sheets = new_row[sheets_columns]
            new_internships.append(new_row_for_sheets)
    
    # Apply updates
    if updates_needed:
        print(f"Updating {len(updates_needed)} existing internships...")
        for update in updates_needed:
            row_data = [update['data'][col] for col in sheets_columns]
            worksheet.update(f"A{update['row']}:{chr(65+len(sheets_columns)-1)}{update['row']}", [row_data])
    
    # Add new internships
    if new_internships:
        print(f"Adding {len(new_internships)} new internships...")
        next_row = len(existing_df) + 2  # +2 for header and 1-indexing
        
        for new_internship in new_internships:
            row_data = [new_internship[col] for col in sheets_columns]
            worksheet.update(f"A{next_row}:{chr(65+len(sheets_columns)-1)}{next_row}", [row_data])
            next_row += 1
    
    print(f"Sync complete! Added {len(new_internships)} new, updated {len(updates_needed)} existing internships.") 