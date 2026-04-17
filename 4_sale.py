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
DEBUG_FILE = "591_debug_data.txt"

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
        cloud_urls = sheets.get_existing_keys("Sale", key_column_index=14)
        if cloud_urls:
            existing_urls = set(cloud_urls)
            print(f"[#] Synced Google Sheets data, total {len(existing_urls)} existing URLs.")


    # ---------------------------------------------
    # --- [優化] 併發控制與資源攔截 ---
    sem = asyncio.Semaphore(3)  # 同時處理 3 個分頁
    save_lock = asyncio.Lock()  # 避免同時寫入 Excel

    async def fetch_one(context, url, index, total):
        async with sem:
            shared_data = {}
            page = await context.new_page()

            # [核心優化] 資源攔截
            async def block_resources(route):
                if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                    await route.abort()
                else:
                    await route.continue_()
            await page.route("**/*", block_resources)

            async def handle_response(response):
                url_res = response.url
                # [偵測] 只抓取包含核心數據的 API，排除推薦/廣告類
                if "recommend" in url_res or "stat" in url_res or "tracker" in url_res:
                    return

                if "/v1/web/sale/detail" in url_res or "/v2/info" in url_res or "/v2/linkInfo" in url_res:
                    if response.status == 200:
                        try:
                            res = await response.json()
                            if isinstance(res, dict):
                                data = res.get("data") if res.get("data") else res
                                if "/v2/info" in url_res:
                                    shared_data["v2_info"] = data
                                elif "/v2/linkInfo" in url_res:
                                    shared_data["v2_link"] = data
                                elif "/v1/web/sale/detail" in url_res:
                                    shared_data["v1_total"] = data
                        except: pass
            
            page.on("response", handle_response)

            try:
                print(f"[*] [{index}/{total}] Processing: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=50000)
                
                # 等待基礎資料到達
                for _ in range(20):
                    if shared_data: break
                    await asyncio.sleep(0.5)
                await asyncio.sleep(2) # 多留點時間給非同步請求

                title = (await page.title()).replace(" - 591售屋網", "").replace("591房屋交易網--", "").strip()
                price, unit_price = "未知", "未知"
                layout, area, age, floor = "未知", "未知", "未知", "未知"
                community, owner, phone, address, email, role = "未知", "未知", "未獲取", "未知", "無", "未知"

                # 優先從 v1_total (最完整的結構) 拿資料
                if "v1_total" in shared_data:
                    d = shared_data["v1_total"]
                    ware = d.get("ware", {})
                    info_attr = d.get("info", {})
                    link = d.get("linkInfo", {})
                    
                    if ware:
                        price = f"{ware.get('price', '未知')}萬"
                        area = f"{ware.get('area', '未知')}坪"
                        community = ware.get("c_name", community)
                        owner = ware.get("linkman", owner)
                        phone = ware.get("mobile", phone)
                        email = ware.get("email", email)
                        unit_price = ware.get("perprice", unit_price)
                    
                    if info_attr:
                        layout = info_attr.get('1', {}).get('Layout', {}).get('value', layout)
                        age = info_attr.get('1', {}).get('HouseAge', {}).get('value', age)
                        floor = info_attr.get('2', {}).get('Floor', {}).get('value', floor)
                        address = info_attr.get('2', {}).get('zAddress', {}).get('value', address)
                    
                    if link:
                        owner = link.get("linkman") or link.get("name") or owner
                        role = link.get("roleName", role)
                        phone = link.get("mobile") or link.get("ware_mobile") or phone

                # 如果 v1 沒拿到，嘗試從 v2 補完
                if "v2_info" in shared_data:
                    info = shared_data["v2_info"].get("houseInfo", {})
                    if info:
                        price = f"{info.get('totalPrice', info.get('price', price))}萬"
                        area = f"{info.get('area', area)}坪"
                        community = info.get("community_name") or info.get("communityName") or community
                        age = f"{info.get('houseage', '未知')}年"
                        layout = f"{info.get('room',0)}房{info.get('hall',0)}廳" if info.get('room') else info.get('layout', layout)

                if "v2_link" in shared_data:
                    link = shared_data["v2_link"]
                    owner = link.get("name", owner)
                    role = link.get("roleName", role)
                    phone = link.get("mobile", phone)

                if "頁面不存在" in title or title == "對不起，" or "物件已下架" in title:
                    print(f"  [!] Detected dead page: {url}")
                elif "收取服務費" in str(role) or "收取服務費" in str(owner):
                    print(f"  [-] Agent detected, skipping: {title[:15]}")
                else:
                    # Posted Time extraction
                    posted_time_text = "Unknown"
                    if "v1_total" in shared_data:
                        d = shared_data["v1_total"]
                        ware = d.get("ware", {}) or {}
                        # Try to find post time or refresh time in JSON
                        raw_time = ware.get("posttime") or ware.get("refreshtime") or ware.get("validdate")
                        if raw_time:
                            posted_time_text = SheetsHelper.parse_591_time(str(raw_time))
                    
                    # If still unknown, try DOM
                    if posted_time_text == "Unknown":
                        for sel in [".publish-info", ".update-info", "[class*='publish']"]:
                            if await page.locator(sel).count() > 0:
                                txt = (await page.locator(sel).first.inner_text()).strip()
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
                    print(f"  [+] Success: {title[:15]} | Price: {price} | Phone: {phone}")
                
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
        
        tasks = []
        for i, url in enumerate(urls_to_process):
            tasks.append(fetch_one(context, url, i + 1, len(urls_to_process)))
        
        await asyncio.gather(*tasks)
        await browser.close()


def save_single(item, sheets=None):
    # Only Sync to Google Sheets
    if sheets and sheets.authenticated:
        sheets.sync_data("Sale", item)


if __name__ == "__main__":
    asyncio.run(extract_sale_details())
