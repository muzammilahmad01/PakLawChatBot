"""
PTA Website PDF Scraper
Downloads all legislation PDFs from Pakistan Telecommunication Authority website
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# Base URL
BASE_URL = "https://pta.gov.pk"

# Categories to scrape
CATEGORIES = {
    "acts": "https://pta.gov.pk/category/act-1397047816-2023-05-30",
    "rules": "https://pta.gov.pk/category/rules-824773436-2023-05-30",
    "regulations": "https://pta.gov.pk/category/regulations-1674158059-2023-05-30",
    "policies": "https://pta.gov.pk/category/policies-1608540600-2023-05-30",
    "regulatory_frameworks": "https://pta.gov.pk/category/regulatory-frameworks-146103707-2023-05-30",
    "guidelines": "https://pta.gov.pk/category/guidelines-1251819379-2023-05-30"
}

# Output directory
OUTPUT_DIR = "../data/pta_laws"

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}


def create_directories():
    """Create output directories for each category"""
    for category in CATEGORIES.keys():
        dir_path = os.path.join(OUTPUT_DIR, category)
        os.makedirs(dir_path, exist_ok=True)
        print(f"[OK] Created directory: {dir_path}")


def get_page_content(url):
    """Fetch page content with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"[WARN] Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    return None


def extract_pdf_links(html_content, base_url):
    """Extract PDF download links from page"""
    pdf_links = []
    
    if not html_content:
        return pdf_links
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all links that point to PDFs
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        
        # Check for PDF links
        if '.pdf' in href.lower() or 'download' in href.lower():
            # Get the full URL
            full_url = urljoin(base_url, href)
            
            # Get link text for naming
            link_text = link.get_text(strip=True) or "Unknown"
            
            pdf_links.append({
                'url': full_url,
                'name': link_text
            })
    
    return pdf_links


def sanitize_filename(name):
    """Create a safe filename from text"""
    # Remove invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces and excessive underscores
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = re.sub(r'_+', '_', safe_name)
    # Limit length
    safe_name = safe_name[:100]
    return safe_name


def download_pdf(url, save_path):
    """Download a PDF file"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
            print(f"[SKIP] Not a PDF: {url}")
            return False
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False


def scrape_category(category_name, category_url):
    """Scrape all PDFs from a category"""
    print(f"\n{'='*60}")
    print(f"Scraping: {category_name.upper()}")
    print(f"URL: {category_url}")
    print('='*60)
    
    # Get page content
    html = get_page_content(category_url)
    if not html:
        print(f"[ERROR] Could not fetch page: {category_url}")
        return 0
    
    # Extract PDF links
    pdf_links = extract_pdf_links(html, BASE_URL)
    print(f"[*] Found {len(pdf_links)} potential PDF links")
    
    # Download each PDF
    downloaded = 0
    for i, pdf_info in enumerate(pdf_links, 1):
        url = pdf_info['url']
        name = pdf_info['name']
        
        # Skip if not a PDF URL
        if '.pdf' not in url.lower():
            continue
        
        # Create filename
        if name and name != "Unknown" and name != "Download":
            filename = sanitize_filename(name) + ".pdf"
        else:
            # Use URL filename
            filename = url.split('/')[-1]
        
        save_path = os.path.join(OUTPUT_DIR, category_name, filename)
        
        # Skip if already exists
        if os.path.exists(save_path):
            print(f"[SKIP] Already exists: {filename}")
            continue
        
        print(f"[{i}/{len(pdf_links)}] Downloading: {filename[:50]}...")
        
        if download_pdf(url, save_path):
            downloaded += 1
            print(f"      [OK] Saved to {save_path}")
        
        # Be polite - don't hammer the server
        time.sleep(1)
    
    print(f"\n[DONE] Downloaded {downloaded} PDFs from {category_name}")
    return downloaded


def scrape_all():
    """Scrape all categories"""
    print("="*60)
    print("PTA Website PDF Scraper")
    print("="*60)
    
    # Create directories
    create_directories()
    
    total_downloaded = 0
    
    # Scrape each category
    for category_name, category_url in CATEGORIES.items():
        downloaded = scrape_category(category_name, category_url)
        total_downloaded += downloaded
    
    # Summary
    print("\n" + "="*60)
    print("[SUCCESS] SCRAPING COMPLETED")
    print("="*60)
    print(f"Total PDFs downloaded: {total_downloaded}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    return total_downloaded


def scrape_single_category(category_name):
    """Scrape a single category"""
    if category_name not in CATEGORIES:
        print(f"[ERROR] Unknown category: {category_name}")
        print(f"Available: {', '.join(CATEGORIES.keys())}")
        return
    
    create_directories()
    scrape_category(category_name, CATEGORIES[category_name])


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        if category == "all":
            scrape_all()
        else:
            scrape_single_category(category)
    else:
        print("Usage: python scrape_pta.py [all|acts|rules|regulations|policies|regulatory_frameworks|guidelines]")
        print("\nExamples:")
        print("  python scrape_pta.py all     - Download from all categories")
        print("  python scrape_pta.py acts    - Download only Acts")
        print("  python scrape_pta.py rules   - Download only Rules")
