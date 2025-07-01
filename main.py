#!/usr/bin/env python3
"""
Internship Automation Main Script

This script automatically syncs internship data from GitHub to Google Sheets
while preserving manual notes and formatting.
"""

from config import get_google_credentials, get_spreadsheet_url, GITHUB_README_URL
from github_data import detect_changes, process_internship_data
from sheets_sync import connect_to_sheet, smart_sync_to_sheets

def main():
    """Main orchestration function"""
    print("🚀 STARTING GOOGLE SHEETS AUTOMATION")
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        credentials = get_google_credentials()
        spreadsheet_url = get_spreadsheet_url()
        
        # Check for changes first
        print("🔍 Checking for changes in source data...")
        if not detect_changes(GITHUB_README_URL):
            print("✅ No changes detected. Automation complete.")
            return
        
        # Connect to Google Sheets
        print("📊 Connecting to Google Sheets...")
        worksheet, existing_df = connect_to_sheet(credentials, spreadsheet_url)
        if worksheet is None:
            print("❌ Failed to connect to Google Sheets")
            return
        
        # Process GitHub data
        print("⚙️ Processing internship data from GitHub...")
        try:
            new_df = process_internship_data(GITHUB_README_URL)
        except Exception as e:
            print(f"❌ Error processing GitHub data: {e}")
            return
        
        # Perform smart sync
        print("🔄 Performing smart sync...")
        smart_sync_to_sheets(worksheet, new_df, existing_df)
        
        print("🎉 Internship automation completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return

if __name__ == "__main__":
    main() 