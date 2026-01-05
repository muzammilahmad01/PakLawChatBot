"""
NADRA Website PDF Scraper
Downloads all legal framework PDFs from National Database and Registration Authority website
"""

import os
import time
import requests
from bs4 import BeautifulSoup
import re

# Base URL
BASE_URL = "https://www.nadra.gov.pk"
LEGAL_FRAMEWORKS_URL = "https://www.nadra.gov.pk/legalFrameworks"

# Output directory
OUTPUT_DIR = "../data/nadra_laws"

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nadra.gov.pk/',
}

# Known download IDs from NADRA website (extracted from page analysis)
# These IDs follow the pattern: https://www.nadra.gov.pk/getDownload/{id}
DOWNLOAD_IDS = {
    "ordinance": [6],  # NADRA Ordinance, 2000
    "rules": [168, 167, 166, 8, 7],  # Rules documents
    "regulations": [285, 305, 304, 284, 204, 203, 147, 146, 145, 144, 143, 10],  # Regulations
    "policies": [223],  # Policies
    "notifications": [16, 15, 14, 13, 12],  # Notifications
    "judgements": [184, 183, 17]  # Judgements
}


def create_directories():
    """Create output directories for each category"""
    for category in DOWNLOAD_IDS.keys():
        dir_path = os.path.join(OUTPUT_DIR, category)
        os.makedirs(dir_path, exist_ok=True)
        print(f"[OK] Created directory: {dir_path}")


def get_filename_from_response(response, doc_id):
    """Extract filename from response headers or create one"""
    # Try to get filename from Content-Disposition header
    content_disposition = response.headers.get('Content-Disposition', '')
    
    if content_disposition:
        # Parse filename from header
        match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
        if match:
            filename = match.group(1).strip('"\'')
            return filename
    
    # Try to get from Content-Type
    content_type = response.headers.get('Content-Type', '')
    
    if 'pdf' in content_type.lower():
        return f"nadra_document_{doc_id}.pdf"
    elif 'zip' in content_type.lower():
        return f"nadra_document_{doc_id}.zip"
    else:
        return f"nadra_document_{doc_id}.pdf"


def download_document(doc_id, save_dir):
    """Download a document by ID"""
    url = f"{BASE_URL}/getDownload/{doc_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=60, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # Get filename
        filename = get_filename_from_response(response, doc_id)
        save_path = os.path.join(save_dir, filename)
        
        # Skip if already exists
        if os.path.exists(save_path):
            print(f"[SKIP] Already exists: {filename}")
            return True, filename
        
        # Check file size
        content_length = response.headers.get('Content-Length')
        if content_length:
            size_mb = int(content_length) / 1024 / 1024
            print(f"       Size: {size_mb:.2f} MB")
        
        # Save file
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, filename
        
    except Exception as e:
        print(f"[ERROR] Download failed for ID {doc_id}: {e}")
        return False, None


def scrape_category(category_name, doc_ids):
    """Download all documents from a category"""
    print(f"\n{'='*60}")
    print(f"Downloading: {category_name.upper()}")
    print(f"Documents: {len(doc_ids)}")
    print('='*60)
    
    save_dir = os.path.join(OUTPUT_DIR, category_name)
    downloaded = 0
    
    for i, doc_id in enumerate(doc_ids, 1):
        print(f"\n[{i}/{len(doc_ids)}] Downloading ID: {doc_id}...")
        
        success, filename = download_document(doc_id, save_dir)
        
        if success:
            downloaded += 1
            if filename:
                print(f"      [OK] Saved: {filename}")
        
        # Be polite - don't hammer the server
        time.sleep(1)
    
    print(f"\n[DONE] Downloaded {downloaded}/{len(doc_ids)} documents from {category_name}")
    return downloaded


def scrape_all():
    """Scrape all categories"""
    print("="*60)
    print("NADRA Website PDF Scraper")
    print("="*60)
    
    # Create directories
    create_directories()
    
    total_downloaded = 0
    
    # Scrape each category
    for category_name, doc_ids in DOWNLOAD_IDS.items():
        downloaded = scrape_category(category_name, doc_ids)
        total_downloaded += downloaded
    
    # Summary
    print("\n" + "="*60)
    print("[SUCCESS] SCRAPING COMPLETED")
    print("="*60)
    print(f"Total documents downloaded: {total_downloaded}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    return total_downloaded


def scrape_single_category(category_name):
    """Scrape a single category"""
    if category_name not in DOWNLOAD_IDS:
        print(f"[ERROR] Unknown category: {category_name}")
        print(f"Available: {', '.join(DOWNLOAD_IDS.keys())}")
        return
    
    create_directories()
    scrape_category(category_name, DOWNLOAD_IDS[category_name])


def discover_new_ids(start_id=1, end_id=350):
    """
    Discover valid download IDs by testing a range.
    Use this to find new documents that may have been added.
    """
    print("="*60)
    print("NADRA Document ID Discovery")
    print(f"Testing IDs from {start_id} to {end_id}")
    print("="*60)
    
    valid_ids = []
    
    for doc_id in range(start_id, end_id + 1):
        url = f"{BASE_URL}/getDownload/{doc_id}"
        try:
            response = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' in content_type.lower() or 'octet-stream' in content_type.lower():
                    print(f"[FOUND] ID {doc_id}: Valid document")
                    valid_ids.append(doc_id)
        except:
            pass
        
        # Progress indicator every 50 IDs
        if doc_id % 50 == 0:
            print(f"[*] Checked up to ID {doc_id}...")
        
        time.sleep(0.2)  # Be polite
    
    print(f"\n[DONE] Found {len(valid_ids)} valid document IDs:")
    print(valid_ids)
    return valid_ids


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "all":
            scrape_all()
        elif arg == "discover":
            # Discover mode - find all valid IDs
            start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            end = int(sys.argv[3]) if len(sys.argv) > 3 else 350
            discover_new_ids(start, end)
        else:
            scrape_single_category(arg)
    else:
        print("Usage: python scrape_nadra.py [all|ordinance|rules|regulations|policies|notifications|judgements|discover]")
        print("\nExamples:")
        print("  python scrape_nadra.py all              - Download all categories")
        print("  python scrape_nadra.py ordinance        - Download only Ordinance")
        print("  python scrape_nadra.py discover 1 400   - Discover valid IDs from 1 to 400")
