import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://kpcode.kp.gov.pk"
DEPT_URL = BASE + "/homepage/dept_wise"

SAVE_DIR = "C:/TEMP_FYP_DATA/kpk_laws"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

os.makedirs(SAVE_DIR, exist_ok=True)


def clean(text):
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return text.replace(" ", "_")


# ============================ DOWNLOAD FILE ============================

def download_pdf(url, path):
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=20)
        r.raise_for_status()

        with open(path, "wb") as f:
            for chunk in r.iter_content(1024 * 50):
                if chunk:
                    f.write(chunk)

        print(f"     ✔ Saved: {path}")
        return True

    except Exception as e:
        print(f"     ❌ Failed: {e}")
        return False


# ============================ GET PDF FROM LAW PAGE ============================

def extract_pdf_link(law_url):
    r = requests.get(law_url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Look for the download button (exact case retained)
    for a in soup.find_all("a", href=True):
        href = a["href"]  # <-- DO NOT lower-case it

        if "uploads" in href and href.endswith(".pdf"):
            return urljoin(BASE, href)

    return None


# ============================ MAIN SCRAPER ============================

def scrape():
    print("Fetching departments...")
    r = requests.get(DEPT_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    departments = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/homepage/search_by_dept/" in href:
            name = a.text.strip()
            url = urljoin(BASE, href)
            departments.append((name, url))

    print(f"Found {len(departments)} departments.\n")

    # ============================ LOOP ALL DEPARTMENTS ============================

    for dept_name, dept_link in departments:
        print(f"\n=== Department: {dept_name} ===")

        safe = clean(dept_name)
        folder = os.path.join(SAVE_DIR, safe)
        os.makedirs(folder, exist_ok=True)

        # Fetch department page
        r = requests.get(dept_link, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Look for law detail pages
        laws = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/homepage/lawDetails/" in href:
                title = a.text.strip()
                url = urljoin(BASE, href)
                laws.append((title, url))

        print(f"   → Found {len(laws)} laws")

        if not laws:
            continue

        # Download each law
        for i, (title, url) in enumerate(laws, start=1):
            print(f"   {i}/{len(laws)} | {title}")

            pdf_url = extract_pdf_link(url)
            if not pdf_url:
                print("     ⚠ No PDF found")
                continue

            file_name = clean(title)[:120] + ".pdf"
            save_path = os.path.join(folder, file_name)

            if os.path.exists(save_path):
                print("     ⏩ Already exists")
                continue

            download_pdf(pdf_url, save_path)

            time.sleep(1 + random.random())


# ============================ RUN ============================

if __name__ == "__main__":
    scrape()
    print("\n✔ DONE")
