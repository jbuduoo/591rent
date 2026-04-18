import asyncio
import pandas as pd
import os
import re
import random
from playwright.async_api import async_playwright
from sheets_helper import SheetsHelper

# 設定
SEARCH_URL = "https://rent.rakuya.com.tw/result?zipcode=220,231,234,235,236,241,242&tab=rkp&usecode=8"
CSV_FILE = "pending_raku_urls.csv"

async def fetch_raku_urls():
    async with async_playwright() as p:
        print("[*] Starting browser (Stealth Mode) to fetch Rakuya Rental URLs...")
        # 使用隨機 User-Agent 避開偵測
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        # --- [優化] 排除已抓取的資料 ---
        existing_urls = set()
        sheets = SheetsHelper()
        if sheets.authenticated:
            # URL 在 Rakuya_Rent 表格的第 6 欄 (Index 6)
            cloud_urls = sheets.get_existing_keys("Rakuya_Rent", key_column_index=6)
            if cloud_urls:
                existing_urls = set(cloud_urls)
                print(f"[#] Synced Google Sheets data, total {len(existing_urls)} existing Rakuya URLs.")

        all_urls = []
        # 抓取前 3 頁
        for p_idx in range(1, 4):
            url = f"{SEARCH_URL}&page={p_idx}"
            print(f"[*] Fetching Rakuya page {p_idx}...")
            
            try:
                # 模擬真人行為：先去首頁再去搜尋頁
                if p_idx == 1:
                    await page.goto("https://www.rakuya.com.tw/", timeout=30000)
                    await asyncio.sleep(random.uniform(1, 2))

                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(random.uniform(2, 4))

                # 檢查是否被 Cloudflare 擋住
                if "Verify you are human" in await page.content() or "稍候" in await page.title():
                    print(f"  [!] Blocked by Cloudflare on page {p_idx}. Skipping...")
                    continue

                # 提取連結 (樂屋網多種可能的選擇器)
                links = await page.locator(".item__content a, .list-item a, a[href*='/item/']").all()
                count_on_page = 0
                for link in links:
                    href = await link.get_attribute("href")
                    if href and "/item/" in href:
                        full_url = href if href.startswith("http") else f"https://rent.rakuya.com.tw{href}"
                        full_url = full_url.split("?")[0]
                        if full_url not in existing_urls and full_url not in all_urls:
                            all_urls.append(full_url)
                            count_on_page += 1
                
                print(f"  [+] Found {count_on_page} new links on this page.")
                if len(links) == 0:
                    break
                    
            except Exception as e:
                print(f"  [!] Error on Rakuya page {p_idx}: {e}")
                break

        await browser.close()

        if all_urls:
            df = pd.DataFrame({"url": all_urls})
            df.to_csv(CSV_FILE, index=False)
            print(f"[#] Saved {len(all_urls)} Rakuya URLs to {CSV_FILE}")
        else:
            if os.path.exists(CSV_FILE):
                os.remove(CSV_FILE)
            print("[!] No new Rakuya URLs found.")

if __name__ == "__main__":
    asyncio.run(fetch_raku_urls())
