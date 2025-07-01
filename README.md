# Google Sheets and GitHub automation for internships tracking


## Info 

This repo pulls data from the famous [https://github.com/vanshb03/Summer2026-Internships](https://github.com/vanshb03/Summer2026-Internships) github repo for internships, cleans up the data and then puts it in Google sheets. It updates every 6 hours, and it makes it easier for anyone to track where they are in the internship process. You can make changes to the google sheets, add Recruiters, notes, etc. 

## File structures

```
📁 application-automation/
├── main.py                 # Main orchestration script - run this!
├── config.py               # Configuration and environment setup
├── github_data.py          # GitHub data fetching and processing
├── sheets_sync.py          # Google Sheets operations and smart sync
├── requirements.txt        # Python dependencies
├── .gitignore             # Files to ignore in git
├── .env                    # Environment variables (create this)
├── credentials.json        # Google service account credentials (create this)
├── data/output.csv         # Local backup of internship data
├── last_hash.txt           # Change detection hash (auto-generated)
└── .github/workflows/
    └── sync.yml            # GitHub Actions automation (runs every 6 hours)
```

### Core Files Explained:
- **`main.py`**: Entry point that orchestrates the entire sync process
- **`config.py`**: Handles all configuration, environment variables, and credentials
- **`github_data.py`**: Fetches and processes internship data from GitHub
- **`sheets_sync.py`**: Smart syncing that preserves your manual notes and formatting
- **`sync.yml`**: GitHub Actions workflow that runs automatically every 6 hours

