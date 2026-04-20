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

# 房仲/代理人關鍵字 (身分)
AGENT_KEYWORDS = ["仲介", "收取服務費", "代理人", "永慶", "信義", "住商", "中信", "東森"]
# 房仲常用標題關鍵字 (如果資料不全則過濾)
SPAM_TITLE_KEYWORDS = ["推薦", "秒殺", "必看", "歡迎看屋", "搶手"]

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
        # URL is at col 13 for Sale 
        cloud_urls = sheets.get_existing_keys("Sale", key_column_index=13)
        if cloud_urls:
            existing_urls = set(cloud_urls)
            print(f"[#] Synced Google Sheets data, total {len(existing_urls)} existing URLs.")

    # --- [優化] 併發控制與資源攔截 ---
    sem = asyncio.Semaphore(2) 
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
                for _ in range(20):
                    if "api_total" in shared_data: break
                    await asyncio.sleep(0.5)
                await asyncio.sleep(2)

                title = (await page.title()).replace(" - 591售屋網", "").replace("591房屋交易網--", "").strip()
                price, unit_price = "未知", "未知"
                layout, area, age, floor = "未知", "未知", "未知", "未知"
                community, owner, phone, address, role = "未知", "未知", "未獲取", "未知", "未知"

                # 1. 優先從 API 拿資料
                api_address = "未知"
                if "api_total" in shared_data:
                    d = shared_data["api_total"]
                    house = d.get("houseInfo", d.get("ware", {})) or {}
                    contact = d.get("contactInfo", d.get("linkInfo", {})) or {}
                    info = d.get("info", {})
                    bread = d.get("bread", {})
                    
                    if house:
                        price = f"{house.get('price', '未知')}萬" if house.get('price') else price
                        unit_price = house.get("perPrice") or house.get("perprice") or unit_price
                        area = f"{house.get('area', '未知')}坪" if house.get('area') else area
                        community = house.get("communityName") or house.get("c_name") or community
                        age = f"{house.get('houseage') or house.get('age', '未知')}年"
                        floor = house.get("floor") or floor
                        layout = house.get("layout") or f"{house.get('room',0)}房{house.get('hall',0)}廳"
                        
                        # [修復] 地址最優邏輯：優先從 info -> zAddress 拿完整地址
                        # Sale API 的 info 通常是字串鍵值 "2", 裡面的 zAddress 欄位最準確
                        g2 = info.get("2") or info.get(2) or {}
                        if isinstance(g2, dict):
                            api_address = g2.get("zAddress", {}).get("value") or "未知"

                        # 備案 1：如果 zAddress 拿不到，從麵包屑 (bread) 組合
                        if api_address == "未知" and bread:
                            b_city = bread.get("region", {}).get("name", "")
                            b_town = bread.get("section", {}).get("name", "")
                            b_street = house.get("street_name", "")
                            b_num = house.get("addr_number", "")
                            api_address = f"{b_city}{b_town}{b_street}{b_num}".strip()

                        # 備案 2：如果還是不行，從 houseInfo 原本的 city/town 欄位組合
                        if len(api_address) < 5:
                            city = house.get("city_name", "")
                            town = house.get("town_name", "")
                            street = house.get("street_name", "")
                            number = house.get("addr_number", "")
                            api_address = f"{city}{town}{street}{number}".strip()
                        
                        # 備案 3：最後才直接看 address (此欄位常誤植為標題)
                        if len(api_address) < 5:
                            api_address = house.get("address") or "未知"

                    if contact:
                        owner = contact.get("name") or contact.get("linkman") or owner
                        role = contact.get("roleName") or contact.get("role") or role
                        phone = contact.get("mobile") or contact.get("phone") or phone

                # 判定地址效力：如果地址與標題完全相同，則視為抓取錯誤 (591 API 常見 Bug)
                if api_address == title or api_address == "未知":
                    address = "未知"
                else:
                    address = api_address

                # 2. 如果 API 沒抓到或地址有誤，嘗試 DOM Fallback
                if price == "未知":
                    for sel in [".info-price-num", ".house-price"]:
                        if await page.locator(sel).count() > 0:
                            price = (await page.locator(sel).first.inner_text()).strip()
                            break
                if address == "未知":
                    for sel in [".info-addr-value", "a.info-addr-tip", ".house-addr", ".address", ".detail-address"]:
                        if await page.locator(sel).count() > 0:
                            address = (await page.locator(sel).first.inner_text()).strip()
                            if address != title: # 再次確認不是標題
                                break
                            else:
                                address = "未知"

                # 3. 處理過濾與儲存
                # [A] 排除失效頁面
                if "頁面不存在" in title or "對不起" in title or "物件已下架" in title or "不存在" in title:
                    print(f"  [!] Detected dead page, skipping: {url}")
                # [B] 排除房仲/代理人 (更嚴格)
                elif any(kw in str(role) for kw in AGENT_KEYWORDS) or any(kw in str(owner) for kw in AGENT_KEYWORDS):
                    print(f"  [-] Agent detected ({role}), skipping: {title[:15]}")
                # [C] 排除身分不明且標題含房仲術語的案子
                elif (role == "未知" or role == "代理人") and any(kw in title for kw in SPAM_TITLE_KEYWORDS):
                    print(f"  [-] Suspected agent title, skipping: {title[:15]}")
                # [D] 排除資料不全的物件 (重要欄位任一為未知則刪除)
                elif price == "未知" or address == "未知" or phone == "未獲取" or address == "":
                    print(f"  [-] Data incomplete (Price:{price}/Addr:{address}/Phone:{phone}), skipping.")
                else:
                    posted_time_text = "Unknown"
                    if "api_total" in shared_data:
                        d = shared_data["api_total"]
                        # 同時考慮 houseInfo 與 ware
                        house_data = d.get("houseInfo", d.get("ware", {})) or {}
                        # 優先抓 posttime (刊登時間)，其次 refreshtime (重新載入/更新時間)
                        raw_time = house_data.get("posttime") or house_data.get("refreshtime")
                        if raw_time:
                            posted_time_text = SheetsHelper.parse_591_time(raw_time)
                    
                    if posted_time_text == "Unknown":
                        # 備案：嘗試從 DOM 拿文字
                        for sel in [".publish-info", ".update-info"]:
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
                    print(f"  [+] Success: {title[:15]} | Addr: {address[:10]} | Price: {price}")
                
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
        # [優化] 如果是失敗資料產生的 Unknown，下次還是要重新抓取
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
