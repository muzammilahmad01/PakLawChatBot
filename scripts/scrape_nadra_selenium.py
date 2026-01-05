"""
NADRA Website PDF Scraper (Selenium Version)
Downloads Regulations PDFs using browser automation
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# URLs
LEGAL_FRAMEWORKS_URL = "https://www.nadra.gov.pk/legalFrameworks"

# Output directory
OUTPUT_DIR = "../data/nadra_laws/regulations"


def setup_driver():
    """Setup Chrome driver with download preferences"""
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    abs_download_path = os.path.abspath(OUTPUT_DIR)
    
    # Chrome options
    chrome_options = Options()
    
    # Set download preferences
    prefs = {
        "download.default_directory": abs_download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,  # Don't open PDF in browser
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Optional: Run headless (no visible browser window)
    # chrome_options.add_argument("--headless")
    
    # Disable automation flags
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Create driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute script to hide automation
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def wait_for_download(timeout=30):
    """Wait for download to complete"""
    time.sleep(timeout)


def scrape_regulations():
    """Scrape regulations tab"""
    print("="*60)
    print("NADRA Regulations PDF Scraper (Selenium)")
    print("="*60)
    
    driver = setup_driver()
    downloaded = 0
    
    try:
        # Navigate to legal frameworks page
        print(f"\n[*] Opening: {LEGAL_FRAMEWORKS_URL}")
        driver.get(LEGAL_FRAMEWORKS_URL)
        
        # Wait for page to load
        time.sleep(3)
        
        # Click on Regulations tab
        print("[*] Looking for Regulations tab...")
        try:
            # Try multiple selectors
            regulations_tab = None
            
            # Try by text
            try:
                regulations_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Regulations')]"))
                )
            except:
                pass
            
            # Try by link text
            if not regulations_tab:
                try:
                    regulations_tab = driver.find_element(By.LINK_TEXT, "Regulations")
                except:
                    pass
            
            # Try by partial link text
            if not regulations_tab:
                try:
                    regulations_tab = driver.find_element(By.PARTIAL_LINK_TEXT, "Regulation")
                except:
                    pass
            
            if regulations_tab:
                print("[*] Clicking Regulations tab...")
                regulations_tab.click()
                time.sleep(2)
            else:
                print("[WARN] Could not find Regulations tab, continuing with current page...")
                
        except Exception as e:
            print(f"[WARN] Error finding Regulations tab: {e}")
        
        # Find all download links
        print("[*] Looking for download links...")
        time.sleep(2)
        
        download_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'getDownload') or contains(text(), 'Download')]")
        
        if not download_links:
            # Try alternative selectors
            download_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='download']")
        
        if not download_links:
            # Get all links and filter
            all_links = driver.find_elements(By.TAG_NAME, "a")
            download_links = [link for link in all_links if 'download' in link.get_attribute('href').lower() or 'download' in link.text.lower()]
        
        print(f"[*] Found {len(download_links)} download links")
        
        # Click each download link
        for i, link in enumerate(download_links, 1):
            try:
                link_text = link.text.strip() or "Unknown"
                link_href = link.get_attribute('href') or ""
                
                print(f"\n[{i}/{len(download_links)}] Downloading: {link_text[:50]}...")
                print(f"    URL: {link_href[:60]}...")
                
                # Scroll to element
                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                time.sleep(0.5)
                
                # Click download
                link.click()
                downloaded += 1
                
                # Wait for download
                time.sleep(3)
                
            except Exception as e:
                print(f"    [ERROR] Failed: {str(e)[:50]}")
                continue
        
        # Wait for all downloads to finish
        print("\n[*] Waiting for downloads to complete...")
        time.sleep(10)
        
        # Summary
        print("\n" + "="*60)
        print("[DONE] SCRAPING COMPLETED")
        print("="*60)
        print(f"Download attempts: {downloaded}")
        print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
        
        # List downloaded files
        files = os.listdir(OUTPUT_DIR)
        pdf_files = [f for f in files if f.endswith('.pdf')]
        print(f"PDF files in directory: {len(pdf_files)}")
        for f in pdf_files[:10]:
            print(f"  - {f}")
        if len(pdf_files) > 10:
            print(f"  ... and {len(pdf_files) - 10} more")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n[*] Closing browser in 5 seconds...")
        time.sleep(5)
        driver.quit()
    
    return downloaded


if __name__ == "__main__":
    scrape_regulations()
