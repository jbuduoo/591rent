import asyncio
import pandas as pd
import os
import re
import random
from playwright.async_api import async_playwright

# 設定
TARGET_URLS = [
    "https://rent.591.com.tw/list?region=3&section=26,39,38,37&shType=host&kind=1",
    "https://rent.591.com.tw/list?region=3&section=26,39,38,37&shType=host&kind=2",
    "https://rent.591.com.tw/list?region=3&section=34,43,44&shType=host&kind=1",
    "https://rent.591.com.tw/list?region=3&section=34,43,44&shType=host&kind=2"
    
]
CSV_FILE = "pending_urls.csv"

async def fetch_urls(pages=10):
    # 1. Initialization: Clear CSV and write header (use utf-8-sig for Excel compatibility)
    print(f"[*] Clearing {CSV_FILE} and preparing new task...")
    with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
        f.write("url\n")
    
    all_found_set = set() # Used to record URLs found in this task to prevent duplicates

    async with async_playwright() as p:
        print(f"[*] Starting browser, preparing to scrape {len(TARGET_URLS)} search URLs...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for u_idx, target_url in enumerate(TARGET_URLS):
            print(f"\n[*] [URL {u_idx + 1}/{len(TARGET_URLS)}] Processing area URL...")
            
            for p_idx in range(pages):
                first_row = p_idx * 30
                current_page_url = f"{target_url}&firstRow={first_row}"
                
                try:
                    print(f"[#] [{p_idx + 1}/{pages}] Fetching: {current_page_url}", flush=True)
                    await page.goto(current_page_url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(5)
                    
                    # Scroll to ensure content loads
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                    await asyncio.sleep(2)

                    links = await page.locator("a.link").all()
                    page_found_count = 0
                    
                    for link in links:
                        url = await link.get_attribute("href")
                        if url and "rent.591.com.tw/" in url:
                            match = re.search(r'/(\d+)', url)
                            if match:
                                case_id = match.group(1)
                                full_url = f"https://rent.591.com.tw/{case_id}"
                                
                                # If it's a newly discovered URL
                                if full_url not in all_found_set:
                                    all_found_set.add(full_url)
                                    page_found_count += 1
                                    
                                    # --- Log and write each link as it is found ---
                                    print(f"  [+] Found new link [{page_found_count}]: {full_url}", flush=True)
                                    try:
                                        with open(CSV_FILE, "a", encoding="utf-8-sig") as f:
                                            f.write(f"{full_url}\n")
                                    except PermissionError:
                                        print(f"  [!] Warning: Cannot write to file, please close Excel if it is open!")
                    
                    print(f"[+] Page {p_idx + 1} completed, added {page_found_count} links.")
                    
                    if page_found_count == 0:
                        print(f"[*] No more links for this search URL.")
                        break

                    await asyncio.sleep(random.uniform(2, 4))

                except Exception as e:
                    print(f"[!] Error on page {p_idx + 1}: {e}")
                    break

        print(f"\n[Finished] Task ended. Total {len(all_found_set)} URLs saved to {CSV_FILE}.")
        await browser.close()



if __name__ == "__main__":
    asyncio.run(fetch_urls())
