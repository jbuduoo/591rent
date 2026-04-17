import asyncio
import os
import re
import random
from playwright.async_api import async_playwright

# Sale settings
TARGET_URL = "https://sale.591.com.tw/?regionid=3&section=38,37&shType=host"
CSV_FILE = "pending_sale_urls.csv"
PAGE_LOG = "3_sale_page_log.txt"

async def fetch_sale_urls(pages=8): # Set a larger range, rely on auto-stop to finish
    # 1. Initialize files
    print(f"[*] Clearing {CSV_FILE} and creating {PAGE_LOG}...")
    with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
        f.write("url\n")
    
    with open(PAGE_LOG, "w", encoding="utf-8") as f:
        f.write("=== 591 Sale URL Scraper (Auto-stop enabled) ===\n\n")
    
    all_found_set = set() 

    async with async_playwright() as p:
        print(f"[*] Starting browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Enter initial page
        print(f"[*] Entering initial URL: {TARGET_URL}")
        await page.goto(TARGET_URL, wait_until="load", timeout=90000)
        await asyncio.sleep(5)

        for p_idx in range(pages):
            try:
                print(f"\n[#] [Page {p_idx + 1}] Loading and scanning content...")
                
                # Human-like scrolling
                for _ in range(6):
                    await page.mouse.wheel(0, 1000)
                    await asyncio.sleep(1.5)
                
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(4)

                # Scrape links
                links = await page.locator("a[href*='/house/detail/']").all()
                total_links = len(links)
                
                with open(PAGE_LOG, "a", encoding="utf-8") as log_f:
                    log_f.write(f"\n--- Page {p_idx + 1} ---\n")
                    log_f.write(f"Current URL: {page.url}\n")
                    
                    page_new_count = 0
                    for link in links:
                        url = await link.get_attribute("href")
                        if not url: continue
                        match = re.search(r'detail/(?:2/)?(\d+)', url)
                        if match:
                            case_id = match.group(1)
                            full_url = f"https://sale.591.com.tw/home/house/detail/2/{case_id}.html"
                            if full_url not in all_found_set:
                                all_found_set.add(full_url)
                                page_new_count += 1
                                log_f.write(f"[NEW] {full_url}\n")
                                with open(CSV_FILE, "a", encoding="utf-8-sig") as f:
                                    f.write(f"{full_url}\n")
                    
                    log_f.write(f"Stats: {page_new_count} new links found.\n")
                    print(f"[+] Page {p_idx + 1} completed, {page_new_count} new found ({total_links} total visible).")

                # Auto-stop check
                if page_new_count == 0:
                    print(f"[Finish] No new items found on this page, ending task early.")
                    break

                # Try clicking "Next"
                if p_idx < pages - 1:
                    next_btn = page.locator("a.pageNext, .pageNext, .page-next, a:has-text('Next')").first
                    if await next_btn.is_visible():
                        print(f"[*] Clicking 'Next' to load more...")
                        await next_btn.scroll_into_view_if_needed()
                        await next_btn.click()
                        await asyncio.sleep(8)
                    else:
                        print(f"[Finish] No 'Next' button found, ending task.")
                        break
                
            except Exception as e:
                print(f"[!] Error occurred: {e}")
                break

        print(f"\n[Finished] Task ended. Total {len(all_found_set)} sale URLs saved.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_sale_urls())
