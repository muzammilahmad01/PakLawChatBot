"""
Pakistan Code Scraper - Federal Laws (pakistancode.gov.pk)
==========================================================
Scrapes all federal laws from the Pakistan Code website, organized by category.
Downloads PDFs for each law into category-specific folders.

Usage:
    python scrape_pakistancode.py                  # Scrape all categories
    python scrape_pakistancode.py --category 1     # Scrape only Criminal Laws (catid=1)
    python scrape_pakistancode.py --dry-run        # List all laws without downloading
    python scrape_pakistancode.py --resume         # Skip already downloaded PDFs

Categories on pakistancode.gov.pk:
    1:  Criminal Laws (69)
    2:  Civil Laws (147)
    3:  Family Laws (22)
    4:  Service Laws (25)
    5:  Labour Laws (41)
    6:  Police Laws (4)
    7:  Companies Laws (9)
    8:  Land/Property Laws (18)
    9:  Islamic/Religious Laws (5)
    10: Banking/Financial Laws (27)
    11: Law of Evidence (1)
    12: Rent Laws (3)
    13: International Laws (7)
    14: Tenancy Laws (0)
    15: Land Reform Laws (2)
    16: Minorities Laws (0)
    17: Excise/Taxation Laws (14)
    18: Military Laws (18)
    19: Health/Medical Laws (18)
    20: Media Laws
    21: Election Laws
    22: Departmental Laws
    23: General Laws
"""

import os
import re
import sys
import time
import json
import random
import argparse
import hashlib
import logging
from datetime import datetime
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup


# ========================== CONFIGURATION ==========================

BASE_URL = "https://pakistancode.gov.pk"
CATEGORY_PAGE = f"{BASE_URL}/english/LGu0xVD.php"

# Save location - relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_SAVE_DIR = os.path.join(PROJECT_ROOT, "data", "pakistan_code")

# All categories with their IDs and URL suffixes
CATEGORIES = {
    1:  {"name": "Criminal_Laws",           "url_suffix": "LGu0xVD-apaUY2Fqa-ag%3D%3D&action=primary&catid=1"},
    2:  {"name": "Civil_Laws",              "url_suffix": "LGu0xVD-apaUY2Fqa-aw%3D%3D&action=primary&catid=2"},
    3:  {"name": "Family_Laws",             "url_suffix": "LGu0xVD-apaUY2Fqa-bA%3D%3D&action=primary&catid=3"},
    4:  {"name": "Service_Laws",            "url_suffix": "LGu0xVD-apaUY2Fqa-bQ%3D%3D&action=primary&catid=4"},
    5:  {"name": "Labour_Laws",             "url_suffix": "LGu0xVD-apaUY2Fqa-bg%3D%3D&action=primary&catid=5"},
    6:  {"name": "Police_Laws",             "url_suffix": "LGu0xVD-apaUY2Fqa-bw%3D%3D&action=primary&catid=6"},
    7:  {"name": "Companies_Laws",          "url_suffix": "LGu0xVD-apaUY2Fqa-cA%3D%3D&action=primary&catid=7"},
    8:  {"name": "Land_Property_Laws",      "url_suffix": "LGu0xVD-apaUY2Fqa-cQ%3D%3D&action=primary&catid=8"},
    9:  {"name": "Islamic_Religious_Laws",  "url_suffix": "LGu0xVD-apaUY2Fqa-cg%3D%3D&action=primary&catid=9"},
    10: {"name": "Banking_Financial_Laws",  "url_suffix": "LGu0xVD-apaUY2Fqa-apY%3D&action=primary&catid=10"},
    11: {"name": "Law_of_Evidence",         "url_suffix": "LGu0xVD-apaUY2Fqa-apc%3D&action=primary&catid=11"},
    12: {"name": "Rent_Laws",               "url_suffix": "LGu0xVD-apaUY2Fqa-apg%3D&action=primary&catid=12"},
    13: {"name": "International_Laws",      "url_suffix": "LGu0xVD-apaUY2Fqa-apk%3D&action=primary&catid=13"},
    14: {"name": "Tenancy_Laws",            "url_suffix": "LGu0xVD-apaUY2Fqa-apo%3D&action=primary&catid=14"},
    15: {"name": "Land_Reform_Laws",        "url_suffix": "LGu0xVD-apaUY2Fqa-aps%3D&action=primary&catid=15"},
    16: {"name": "Minorities_Laws",         "url_suffix": "LGu0xVD-apaUY2Fqa-apw%3D&action=primary&catid=16"},
    17: {"name": "Excise_Taxation_Laws",    "url_suffix": "LGu0xVD-apaUY2Fqa-ap0%3D&action=primary&catid=17"},
    18: {"name": "Military_Laws",           "url_suffix": "LGu0xVD-apaUY2Fqa-ap4%3D&action=primary&catid=18"},
    19: {"name": "Health_Medical_Laws",     "url_suffix": "LGu0xVD-apaUY2Fqa-ap8%3D&action=primary&catid=19"},
    20: {"name": "Media_Laws",              "url_suffix": "LGu0xVD-apaUY2Fqa-a5Y%3D&action=primary&catid=20"},
    21: {"name": "Election_Laws",           "url_suffix": "LGu0xVD-apaUY2Fqa-a5c%3D&action=primary&catid=21"},
    22: {"name": "Departmental_Laws",       "url_suffix": "LGu0xVD-apaUY2Fqa-a5g%3D&action=primary&catid=22"},
    23: {"name": "General_Laws",            "url_suffix": "LGu0xVD-apaUY2Fqa-a5k%3D&action=primary&catid=23"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
}

# Rate limiting
MIN_DELAY = 1.5   # Minimum seconds between requests
MAX_DELAY = 3.0   # Maximum seconds between requests
MAX_RETRIES = 3   # Max retries per request


# ========================== LOGGING ==========================

def setup_logging(save_dir):
    """Setup logging to both console and file"""
    log_file = os.path.join(save_dir, "scraper.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


# ========================== UTILITIES ==========================

def clean_filename(text, max_length=150):
    """Clean text to make it a safe filename"""
    # Remove/replace problematic characters
    text = text.strip()
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip('. ')
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rstrip()
    
    return text


def polite_delay():
    """Wait a random amount of time to be polite to the server"""
    delay = MIN_DELAY + random.random() * (MAX_DELAY - MIN_DELAY)
    time.sleep(delay)


def make_request(url, logger, retries=MAX_RETRIES):
    """Make an HTTP request with retry logic"""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"   Request failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                wait_time = attempt * 5  # Exponential backoff
                logger.info(f"   Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"   All {retries} attempts failed for: {url}")
                return None
    return None


# ========================== SCRAPER FUNCTIONS ==========================

def get_category_laws(cat_id, cat_info, logger):
    """
    Fetch all law links from a category page.
    
    Returns:
        List of dicts: [{"title": "...", "url": "...", "promulgation_info": "..."}, ...]
    """
    url = f"{BASE_URL}/english/{cat_info['url_suffix']}"
    logger.info(f"Fetching category page: {cat_info['name']} (catid={cat_id})")
    
    response = make_request(url, logger)
    if not response:
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    laws = []
    seen_urls = set()
    
    # Law links follow the pattern: UY2FqaJw1-...-sg-jjj...
    # They are different from category links (LGu0xVD-...) and sidebar links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        title = a_tag.get_text(strip=True)
        
        # Skip empty titles
        if not title:
            continue
        
        # Match only law detail page links (pattern: UY2FqaJw1-...-sg-...)
        # These are the actual law links, NOT:
        # - Category links (LGu0xVD-...)
        # - Navigation links (index.php, Rki82H.php, etc.)
        # - Sidebar links (pdffiles/...)
        if "UY2FqaJw1-" in href and "-sg-" in href:
            full_url = urljoin(f"{BASE_URL}/english/", href)
            
            # Deduplicate by URL
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                
                # Try to extract promulgation info from sibling elements
                promulgation_info = ""
                parent = a_tag.parent
                if parent:
                    parent_text = parent.get_text(strip=True)
                    if "Promulgation" in parent_text:
                        promulgation_info = parent_text
                
                laws.append({
                    "title": title,
                    "url": full_url,
                    "promulgation_info": promulgation_info,
                })
    
    logger.info(f"   Found {len(laws)} laws in {cat_info['name']}")
    return laws


def extract_pdf_url_from_law_page(law_url, logger):
    """
    Visit a law's detail page and extract the PDF download URL.
    
    The Pakistan Code website structure:
    - Each law page has a "Print/Download PDF" tab
    - The PDF is served from pdffiles/administrator<hash>.pdf
    - Sometimes the PDF link is in JavaScript or an iframe
    
    Returns:
        str: PDF URL or None if not found
    """
    response = make_request(law_url, logger)
    if not response:
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    html_text = response.text
    
    # Strategy 1: Look for direct PDF links in the page
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "pdffiles" in href and href.endswith(".pdf"):
            return urljoin(BASE_URL, href)
    
    # Strategy 2: Look for PDF links in iframes
    for iframe in soup.find_all("iframe", src=True):
        src = iframe["src"]
        if "pdffiles" in src and src.endswith(".pdf"):
            return urljoin(BASE_URL, src)
    
    # Strategy 3: Look for PDF URLs in JavaScript/embedded content
    pdf_pattern = r'(?:href|src|url)\s*[=:]\s*["\']?([^"\'>\s]*pdffiles[^"\'>\s]*\.pdf)'
    matches = re.findall(pdf_pattern, html_text, re.IGNORECASE)
    if matches:
        return urljoin(BASE_URL, matches[0])
    
    # Strategy 4: Look for any .pdf link in the page
    pdf_pattern2 = r'["\']([^"\']*\.pdf)["\']'
    matches = re.findall(pdf_pattern2, html_text)
    for match in matches:
        if "pdffiles" in match or "administrator" in match:
            return urljoin(BASE_URL, match)
    
    # Strategy 5: Check the #download section - the PDF might be loaded via AJAX
    # The page uses UY2FqaJw2.php?action=get&apaUY2Fqa=<id>&con= for dynamic loading
    # Try to extract the law ID and construct the PDF request
    download_pattern = r'UY2FqaJw2\.php\?action=get&apaUY2Fqa=([^&"\']+)'
    id_matches = re.findall(download_pattern, html_text)
    
    if id_matches:
        law_id = id_matches[0]
        # Try fetching the dynamic content that contains the PDF link
        ajax_url = f"{BASE_URL}/english/UY2FqaJw2.php?action=get&apaUY2Fqa={law_id}&con="
        ajax_response = make_request(ajax_url, logger)
        if ajax_response and ajax_response.text:
            pdf_matches = re.findall(r'([^"\'>\s]*pdffiles[^"\'>\s]*\.pdf)', ajax_response.text)
            if pdf_matches:
                return urljoin(BASE_URL, pdf_matches[0])
            
            # Also check for any PDF link in the AJAX response
            pdf_matches2 = re.findall(r'["\']([^"\']*\.pdf)["\']', ajax_response.text)
            for match in pdf_matches2:
                return urljoin(BASE_URL, match)
    
    # Strategy 6: Try the print/download tab directly
    # Some pages have a different URL pattern for PDF download
    # Try constructing the download URL from the law page URL
    download_section_url = law_url + "#download"
    
    return None


def download_pdf(pdf_url, save_path, logger):
    """Download a PDF file"""
    try:
        response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=60)
        response.raise_for_status()
        
        # Verify it's actually a PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and "octet-stream" not in content_type.lower():
            # Check the first bytes for PDF magic number
            first_bytes = b""
            for chunk in response.iter_content(1024):
                first_bytes = chunk
                break
            
            if not first_bytes.startswith(b"%PDF"):
                logger.warning(f"   Not a valid PDF (Content-Type: {content_type})")
                return False
            
            # Write the first chunk and the rest
            with open(save_path, "wb") as f:
                f.write(first_bytes)
                for chunk in response.iter_content(1024 * 50):
                    if chunk:
                        f.write(chunk)
        else:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024 * 50):
                    if chunk:
                        f.write(chunk)
        
        file_size = os.path.getsize(save_path) / 1024  # KB
        logger.info(f"   [OK] Downloaded: {os.path.basename(save_path)} ({file_size:.1f} KB)")
        return True
        
    except Exception as e:
        logger.error(f"   [FAIL] Download failed: {e}")
        if os.path.exists(save_path):
            os.remove(save_path)
        return False


# ========================== MAIN SCRAPER ==========================

def scrape_category(cat_id, cat_info, save_dir, logger, dry_run=False, resume=True):
    """
    Scrape all laws from a single category.
    
    Args:
        cat_id: Category ID
        cat_info: Dict with name and url_suffix
        save_dir: Base directory to save PDFs
        logger: Logger instance
        dry_run: If True, only list laws without downloading
        resume: If True, skip already downloaded PDFs
    
    Returns:
        dict: Stats about the scraping results
    """
    cat_name = cat_info["name"]
    cat_dir = os.path.join(save_dir, cat_name)
    os.makedirs(cat_dir, exist_ok=True)
    
    stats = {
        "category": cat_name,
        "cat_id": cat_id,
        "total_laws": 0,
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "no_pdf": 0,
        "laws": []
    }
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Category: {cat_name} (ID: {cat_id})")
    logger.info(f"{'='*70}")
    
    # Step 1: Get all law links from category page
    laws = get_category_laws(cat_id, cat_info, logger)
    stats["total_laws"] = len(laws)
    
    if not laws:
        logger.info(f"   No laws found in {cat_name}")
        return stats
    
    if dry_run:
        logger.info(f"\n   [DRY RUN] Laws in {cat_name}:")
        for i, law in enumerate(laws, 1):
            logger.info(f"   {i:3d}. {law['title']}")
            stats["laws"].append({"title": law["title"], "url": law["url"]})
        return stats
    
    # Step 2: Process each law
    for i, law in enumerate(laws, 1):
        title = law["title"]
        law_url = law["url"]
        
        # Create safe filename
        safe_name = clean_filename(title)
        pdf_filename = f"{safe_name}.pdf"
        pdf_path = os.path.join(cat_dir, pdf_filename)
        
        logger.info(f"\n   [{i}/{len(laws)}] {title}")
        
        # Check if already downloaded (resume mode)
        if resume and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            if file_size > 0:
                logger.info(f"   [SKIP] Already exists ({file_size/1024:.1f} KB), skipping")
                stats["skipped"] += 1
                stats["laws"].append({
                    "title": title,
                    "url": law_url,
                    "status": "skipped",
                    "file": pdf_filename
                })
                continue
        
        # Step 2a: Visit law page to find PDF URL
        polite_delay()
        pdf_url = extract_pdf_url_from_law_page(law_url, logger)
        
        if not pdf_url:
            logger.warning(f"   [WARN] No PDF link found for: {title}")
            stats["no_pdf"] += 1
            stats["laws"].append({
                "title": title,
                "url": law_url,
                "status": "no_pdf_found"
            })
            continue
        
        # Step 2b: Download the PDF
        polite_delay()
        success = download_pdf(pdf_url, pdf_path, logger)
        
        if success:
            stats["downloaded"] += 1
            stats["laws"].append({
                "title": title,
                "url": law_url,
                "pdf_url": pdf_url,
                "status": "downloaded",
                "file": pdf_filename
            })
        else:
            stats["failed"] += 1
            stats["laws"].append({
                "title": title,
                "url": law_url,
                "pdf_url": pdf_url,
                "status": "failed"
            })
    
    # Summary for this category
    logger.info(f"\n   --- {cat_name} Summary ---")
    logger.info(f"   Total laws:  {stats['total_laws']}")
    logger.info(f"   Downloaded:  {stats['downloaded']}")
    logger.info(f"   Skipped:     {stats['skipped']}")
    logger.info(f"   No PDF:      {stats['no_pdf']}")
    logger.info(f"   Failed:      {stats['failed']}")
    
    return stats


def scrape_all(save_dir, categories_to_scrape=None, dry_run=False, resume=True):
    """
    Main scraper function - scrapes all (or specified) categories.
    
    Args:
        save_dir: Directory to save downloaded PDFs
        categories_to_scrape: List of category IDs to scrape (None = all)
        dry_run: If True, only list laws without downloading
        resume: If True, skip already downloaded PDFs
    """
    os.makedirs(save_dir, exist_ok=True)
    logger = setup_logging(save_dir)
    
    logger.info("=" * 70)
    logger.info("Pakistan Code Scraper - Federal Laws")
    logger.info(f"Website: {BASE_URL}")
    logger.info(f"Save directory: {save_dir}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'DOWNLOAD'}")
    logger.info(f"Resume: {resume}")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # Determine which categories to scrape
    if categories_to_scrape:
        cats_to_process = {k: v for k, v in CATEGORIES.items() if k in categories_to_scrape}
    else:
        cats_to_process = CATEGORIES
    
    logger.info(f"\nCategories to scrape: {len(cats_to_process)}")
    for cat_id, cat_info in cats_to_process.items():
        logger.info(f"   {cat_id:2d}. {cat_info['name']}")
    
    # Scrape each category
    all_stats = []
    total_downloaded = 0
    total_laws = 0
    total_failed = 0
    total_no_pdf = 0
    
    for cat_id, cat_info in cats_to_process.items():
        try:
            stats = scrape_category(cat_id, cat_info, save_dir, logger, dry_run, resume)
            all_stats.append(stats)
            total_downloaded += stats["downloaded"]
            total_laws += stats["total_laws"]
            total_failed += stats["failed"]
            total_no_pdf += stats["no_pdf"]
        except Exception as e:
            logger.error(f"\n[ERROR] Error scraping {cat_info['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # Be extra polite between categories
        if not dry_run:
            time.sleep(3)
    
    # Final Summary
    logger.info(f"\n\n{'='*70}")
    logger.info("SCRAPING COMPLETE - FINAL SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"Total categories scraped: {len(all_stats)}")
    logger.info(f"Total laws found:         {total_laws}")
    logger.info(f"Total downloaded:         {total_downloaded}")
    logger.info(f"Total failed:             {total_failed}")
    logger.info(f"Total no PDF found:       {total_no_pdf}")
    logger.info(f"Save directory:           {save_dir}")
    logger.info(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Per-category breakdown
    logger.info(f"\nPer-Category Breakdown:")
    logger.info(f"{'Category':<30s} {'Total':>6s} {'Downloaded':>11s} {'Failed':>7s} {'No PDF':>7s}")
    logger.info("-" * 65)
    for stats in all_stats:
        logger.info(
            f"{stats['category']:<30s} {stats['total_laws']:>6d} "
            f"{stats['downloaded']:>11d} {stats['failed']:>7d} {stats['no_pdf']:>7d}"
        )
    
    # Save results as JSON for reference
    results_file = os.path.join(save_dir, "scrape_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "scrape_date": datetime.now().isoformat(),
            "website": BASE_URL,
            "total_laws": total_laws,
            "total_downloaded": total_downloaded,
            "total_failed": total_failed,
            "categories": all_stats
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nResults saved to: {results_file}")
    
    return all_stats


# ========================== CLI ==========================

def main():
    parser = argparse.ArgumentParser(
        description="Scrape Federal Laws from Pakistan Code (pakistancode.gov.pk)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_pakistancode.py                     # Scrape all categories
  python scrape_pakistancode.py --dry-run           # List all laws (no download)
  python scrape_pakistancode.py --category 1        # Only Criminal Laws
  python scrape_pakistancode.py --category 1 3 5    # Criminal, Family, Labour
  python scrape_pakistancode.py --resume            # Resume interrupted download
  python scrape_pakistancode.py --list-categories   # Show all categories
  python scrape_pakistancode.py --output ./my_laws  # Custom save directory
        """
    )
    
    parser.add_argument(
        "--category", "-c",
        type=int, nargs="+",
        help="Category ID(s) to scrape (default: all). Use --list-categories to see IDs."
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=DEFAULT_SAVE_DIR,
        help=f"Output directory (default: {DEFAULT_SAVE_DIR})"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Only list laws without downloading PDFs"
    )
    
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        default=True,
        help="Skip already downloaded PDFs (default: True)"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-download all PDFs, even if they already exist"
    )
    
    parser.add_argument(
        "--list-categories", "-l",
        action="store_true",
        help="List all available categories and exit"
    )
    
    args = parser.parse_args()
    
    # List categories
    if args.list_categories:
        print("\nAvailable Categories on pakistancode.gov.pk:")
        print("-" * 50)
        for cat_id, cat_info in CATEGORIES.items():
            print(f"  {cat_id:2d}. {cat_info['name']}")
        print(f"\nTotal: {len(CATEGORIES)} categories")
        return
    
    # Validate category IDs
    if args.category:
        invalid = [c for c in args.category if c not in CATEGORIES]
        if invalid:
            print(f"Error: Invalid category ID(s): {invalid}")
            print(f"Valid IDs: {list(CATEGORIES.keys())}")
            sys.exit(1)
    
    # Handle resume flag
    resume = not args.no_resume
    
    # Run scraper
    print(f"\n[*] Pakistan Code Scraper")
    print(f"    Save to: {args.output}")
    print(f"    Mode: {'DRY RUN' if args.dry_run else 'DOWNLOAD'}")
    
    if not args.dry_run:
        print(f"\n[!] This will download PDFs from pakistancode.gov.pk")
        print(f"   The scraper includes delays to be respectful to the server.")
        response = input("   Continue? (y/n): ").strip().lower()
        if response != "y":
            print("   Aborted.")
            return
    
    scrape_all(
        save_dir=args.output,
        categories_to_scrape=args.category,
        dry_run=args.dry_run,
        resume=resume
    )


if __name__ == "__main__":
    main()
