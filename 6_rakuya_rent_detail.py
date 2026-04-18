import asyncio
import pandas as pd
import os
import random
import re
from playwright.async_api import async_playwright
from sheets_helper import SheetsHelper

# 設定
CSV_FILE = "pending_raku_urls.csv"

async def extract_raku_details():
    if not os.path.exists(CSV_FILE):
        print(f"[!] Error: Cannot find {CSV_FILE}")
        return

    try:
        df_pending = pd.read_csv(CSV_FILE)
    except: return
    if len(df_pending) == 0: return

    # --- [優化] 只從 Google Sheets 同步已有的網址 ---
    existing_urls = set()
    sheets = SheetsHelper()
    if sheets.authenticated:
        # URL is at col 6 for Rakuya_Rent (1-based index)
        cloud_urls = sheets.get_existing_keys("Rakuya_Rent", key_column_index=6)
        if cloud_urls:
            existing_urls = set(cloud_urls)
            print(f"[#] Synced Google Sheets data, total {len(existing_urls)} existing Rakuya URLs.")

    # --- [優化] 併發控制 ---
    sem = asyncio.Semaphore(1) # Rakuya 比較嚴格，一次處理一個
    save_lock = asyncio.Lock()

    async def fetch_one(context, url, index, total):
        async with sem:
            page = await context.new_page()

            async def block_resources(route):
                if route.request.resource_type in ["image", "font", "media"]:
                    await route.abort()
                else:
                    await route.continue_()
            await page.route("**/*", block_resources)

            try:
                print(f"[*] [{index}/{total}] Processing Rakuya: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(3, 5))

                # 1. 提取基本資訊
                title = "未知"
                for sel in [".obj-name", "h1.object_name", ".detail-title", "h1"]:
                    if await page.locator(sel).count() > 0:
                        title = (await page.locator(sel).first.inner_text()).strip()
                        break
                
                price = "未知"
                for sel in [".price-box .num", ".price_box b", ".item-price b", "b:has-text('元/月')"]:
                    if await page.locator(sel).count() > 0:
                        price = (await page.locator(sel).first.inner_text()).strip()
                        break

                address = "未知"
                for sel in [".f-address", ".item-info-detail .address", ".address"]:
                    if await page.locator(sel).count() > 0:
                        address = (await page.locator(sel).first.inner_text()).strip()
                        break

                owner = "未知"
                for sel in [".owner-name", ".contact-name", ".contact-info .name"]:
                    if await page.locator(sel).count() > 0:
                        owner = (await page.locator(sel).first.inner_text()).strip()
                        break

                phone = "未獲取"
                # 嘗試顯示電話
                try:
                    for btn_sel in [".show-phone", "button:has-text('顯示電話')", ".phone_box"]:
                        if await page.locator(btn_sel).count() > 0:
                            await page.locator(btn_sel).first.click()
                            await asyncio.sleep(1.5)
                            break
                except: pass

                for sel in [".phone-num", ".tel-number", ".phone_box b", "span:has-text('09')"]:
                    if await page.locator(sel).count() > 0:
                        txt_ph = await page.locator(sel).first.inner_text()
                        m = re.search(r'(09\d{2}-\d{3}-\d{3}|09\d{8,})', str(txt_ph))
                        if m:
                            phone = str(m.group(1))
                            break

                posted_time = "未知"
                for sel in [".update-time", ".updated-at", "span:has-text('更新時間')"]:
                    if await page.locator(sel).count() > 0:
                        posted_time = (await page.locator(sel).first.inner_text()).replace("更新時間：", "").strip()
                        break

                results = {
                    "案件名稱": title, 
                    "租金": price, 
                    "地址": address, 
                    "屋主/聯絡人": owner,
                    "電話": phone, 
                    "網址": url,
                    "發佈時間": posted_time,
                    "抓取時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
                
                # [過濾] 如果資料過於殘缺則略過
                if price == "未知" or address == "未知" or "仲介" in str(owner):
                    print(f"  [-] Incomplete or Agent, skipping: {title[:10]}")
                else:
                    async with save_lock:
                        save_single(results, sheets)
                    print(f"  [+] Success Rakuya: {title[:10]} | Price: {price}")
                
                await asyncio.sleep(random.uniform(3, 6))
            except Exception as e:
                print(f"  [x] Error Rakuya ({url}): {e}")
            finally:
                await page.close()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        )
        urls_all = df_pending["url"].tolist()
        urls_to_process = [u for u in urls_all if str(u) not in existing_urls]
        print(f"Pending Rakuya Details: Total {len(all_urls)}, To scrape {len(urls_to_process)}.")
        tasks = [fetch_one(context, url, i + 1, len(urls_to_process)) for i, url in enumerate(urls_to_process)]
        await asyncio.gather(*tasks)
        await browser.close()

def save_single(item, sheets=None):
    if sheets and sheets.authenticated:
        sheets.sync_data("Rakuya_Rent", item)

if __name__ == "__main__":
    asyncio.run(extract_raku_details())
 Riverside
