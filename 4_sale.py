import asyncio
import pandas as pd
import os
import random
import re
import json
from playwright.async_api import async_playwright
from sheets_helper import SheetsHelper

# 設定
CSV_FILE = "pending_sale_urls.csv"

async def extract_sale_details():
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
        # URL is at col 12 for Sale 
        cloud_urls = sheets.get_existing_keys("Sale", key_column_index=14)
        if cloud_urls:
            existing_urls = set(cloud_urls)
            print(f"[#] Synced Google Sheets data, total {len(existing_urls)} existing URLs.")

    # --- [優化] 併發控制與資源攔截 ---
    sem = asyncio.Semaphore(2) # 減少併發以提高穩定性
    save_lock = asyncio.Lock()

    async def fetch_one(context, url, index, total):
        async with sem:
            shared_data = {}
            page = await context.new_page()

            async def block_resources(route):
                if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                    await route.abort()
                else:
                    await route.continue_()
            await page.route("**/*", block_resources)

            async def handle_response(response):
                url_res = response.url
                if "/v1/web/sale/detail" in url_res or "/v2/info" in url_res:
                    if response.status == 200:
                        try:
                            res = await response.json()
                            if isinstance(res, dict):
                                data = res.get("data") if res.get("data") else res
                                shared_data["api_total"] = data
                        except: pass
            
            page.on("response", handle_response)

            try:
                print(f"[*] [{index}/{total}] Processing: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # 等待資料到達
                for _ in range(15):
                    if "api_total" in shared_data: break
                    await asyncio.sleep(0.5)
                await asyncio.sleep(1.5)

                title = (await page.title()).replace(" - 591售屋網", "").replace("591房屋交易網--", "").strip()
                price, unit_price = "未知", "未知"
                layout, area, age, floor = "未知", "未知", "未知", "未知"
                community, owner, phone, address, role = "未知", "未知", "未獲取", "未知", "未知"

                # 1. 優先從 API (api_total) 拿資料
                if "api_total" in shared_data:
                    d = shared_data["api_total"]
                    # 591 Sale API 結構通常有 houseInfo 跟 contactInfo
                    house = d.get("houseInfo", d.get("ware", {})) or {}
                    contact = d.get("contactInfo", d.get("linkInfo", {})) or {}
                    breadcrumb = d.get("breadcrumb", []) # 用來補地址
                    
                    if house:
                        price = f"{house.get('price', '未知')}萬"
                        unit_price = house.get("perPrice") or house.get("perprice") or unit_price
                        area = f"{house.get('area', '未知')}坪"
                        community = house.get("communityName") or house.get("c_name") or community
                        age = f"{house.get('houseage') or house.get('age', '未知')}年"
                        floor = house.get("floor") or floor
                        layout = house.get("layout") or f"{house.get('room',0)}房{house.get('hall',0)}廳"
                        address = house.get("address") or address
                    
                    if contact:
                        owner = contact.get("name") or contact.get("linkman") or owner
                        role = contact.get("roleName") or contact.get("role") or role
                        phone = contact.get("mobile") or contact.get("phone") or phone

                # 2. 如果 API 沒抓到，嘗試 DOM Fallback
                if price == "未知":
                    for sel in [".info-price-num", ".house-price"]:
                        if await page.locator(sel).count() > 0:
                            price = (await page.locator(sel).first.inner_text()).strip()
                            break
                
                if area == "未知":
                    for sel in [".info-floor-key:has-text('坪數') + .info-floor-value", ".house-info span:has-text('坪')"]:
                        if await page.locator(sel).count() > 0:
                            area = (await page.locator(sel).first.inner_text()).strip()
                            break

                # 3. Posted Time extraction
                posted_time_text = "Unknown"
                if "api_total" in shared_data:
                    house = shared_data["api_total"].get("houseInfo", {})
                    raw_time = house.get("posttime") or house.get("refreshtime")
                    if raw_time:
                        posted_time_text = SheetsHelper.parse_591_time(str(raw_time))
                
                if posted_time_text == "Unknown":
                    # 鎖定在詳細資訊區塊，避免抓到 Header 的「會員中心」
                    # 591 售屋詳細頁面的發佈日期通常在 class="publish-info" 或特定 span
                    for sel in [".publish-info", ".update-info", ".house-index span:has-text('更新')"]:
                        container = page.locator(".detail-info-box") if await page.locator(".detail-info-box").count() > 0 else page
                        if await container.locator(sel).count() > 0:
                            txt = (await container.locator(sel).first.inner_text()).strip()
                            posted_time_text = SheetsHelper.parse_591_time(txt)
                            break
                
                results = {
                    "案件名稱": title, "總價": price, "單價": unit_price,
                    "格局": layout, "坪數": area, "屋齡": age, "樓層": floor,
                    "社區": community, "地址": address, "屋主/聯絡人": owner,
                    "身分": role, "電話": phone, "網址": url,
                    "發佈時間": posted_time_text,
                    "抓取時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
                
                async with save_lock:
                    save_single(results, sheets)
                print(f"  [+] Success: {title[:15]} | Price: {price} | Time: {posted_time_text}")
                
                await asyncio.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"  [x] Error ({url}): {e}")
            finally:
                await page.close()

    async with async_playwright() as p:
        print(f"Starting browser (headless mode)...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        urls_all = df_pending["url"].tolist()
        urls_to_process = [u for u in urls_all if str(u) not in existing_urls]
        print(f"Pending list: Total {len(urls_all)}, To scrape {len(urls_to_process)}.")
        tasks = [fetch_one(context, url, i + 1, len(urls_to_process)) for i, url in enumerate(urls_to_process)]
        await asyncio.gather(*tasks)
        await browser.close()

def save_single(item, sheets=None):
    if sheets and sheets.authenticated:
        sheets.sync_data("Sale", item)

if __name__ == "__main__":
    asyncio.run(extract_sale_details())
