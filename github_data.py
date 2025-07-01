import requests
import hashlib
import re
import os
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup

def get_readme_content(url):
    """Fetch the raw README.md content from GitHub"""
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def detect_changes(url):
    """Detect whether the raw README.md has changed"""
    readme_content = get_readme_content(url)
    readme_hash = hashlib.sha256(readme_content.encode()).hexdigest()
    hash_path = "last_hash.txt"
    
    # Check if hash file exists and read last hash
    last_hash = ""
    if os.path.exists(hash_path):
        with open(hash_path, "r") as f:
            last_hash = f.read().strip()
    
    # Compare hashes
    if readme_hash == last_hash:
        print("No changes detected in source data")
        return False
    
    # Save the new hash
    with open(hash_path, "w") as f:
        f.write(readme_hash)
    
    print("Changes detected in source data")
    return True

def extract_internship_table(readme_content):
    """Extract the internship markdown table from README content"""
    pattern = r'\| Company \| Role \| Location \| Application/Link \| Date Posted \|\n\|[-| ]+\|\n((?:\|.*\|\n?)*)'
    
    match = re.search(pattern, readme_content)
    if not match:
        raise Exception("Internship table not found in README")
    
    table_body = match.group(1)
    full_table = (
        "| Company | Role | Location | Application/Link | Date Posted |\n"
        "| ------- | ---- | -------- | ---------------- | ----------- |\n"
        + table_body
    )
    
    return full_table

def parse_markdown_table(markdown_table):
    """Parse markdown table into pandas DataFrame"""
    buffer = StringIO(markdown_table)
    df = pd.read_csv(buffer, sep="|", engine="python", skipinitialspace=True)
    
    # Clean up the dataframe
    df = df.dropna(axis=1, how="all")
    df = df.iloc[1:].reset_index(drop=True)
    df.columns = [c.strip() for c in df.columns]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df

def handle_company_continuations(df):
    """Handle rows where Company is '↳' (continuation of previous company)"""
    for i in range(len(df)):
        if df.loc[i, "Company"].strip() == "↳":
            df.loc[i, "Company"] = df.loc[i-1, "Company"]

def clean_html_tags(text):
    """Clean HTML tags from text fields"""
    if pd.isna(text):
        return text
    return BeautifulSoup(text, "html.parser").get_text(separator=", ")

def extract_link_from_html(html):
    """Extract actual URL from HTML link tags"""
    if pd.isna(html):
        return html
    match = re.search(r'href="([^"]+)"', html)
    return match.group(1) if match else html

def normalize_text(text):
    """Normalize strings for consistent comparison"""
    return re.sub(r'\s+', ' ', text.strip().lower()) if isinstance(text, str) else ''

def generate_unique_key(row):
    """Generate unique key for each internship posting"""
    return "|".join([
        normalize_text(row["Company"]),
        normalize_text(row["Role"]),
        normalize_text(row["Location"]),
        normalize_text(row["Application/Link"]),
        normalize_text(row["Date Posted"]),
        normalize_text(row.get("Recruiters", "")),
        normalize_text(row.get("Notes", "")),
    ])

def process_internship_data(url):
    """Main function to process internship data from GitHub"""
    print("Fetching data from GitHub...")
    
    # Get README content
    readme_content = get_readme_content(url)
    
    # Extract and parse table
    markdown_table = extract_internship_table(readme_content)
    df = parse_markdown_table(markdown_table)
    
    # Add manual tracking columns
    df['Recruiters'] = ""
    df['Notes'] = ""
    
    print(f"Extracted {len(df)} internships from GitHub")
    
    # Process the data
    handle_company_continuations(df)
    df["Location"] = df["Location"].apply(clean_html_tags)
    df["Application/Link"] = df["Application/Link"].apply(extract_link_from_html)
    df["unique_key"] = df.apply(generate_unique_key, axis=1)
    
    # Save backup to local CSV
    df.to_csv('data/output.csv', sep=",", index=False)
    
    return df 