import asyncio
import pandas as pd
import os
import random
import re
import json
from playwright.async_api import async_playwright
from sheets_helper import SheetsHelper

# 設定
CSV_FILE = "pending_urls.csv"

# 重新抓取現有 ID 資料
RE_SCRAPE_ALL = False 

async def extract_from_bg_data(p, s_data):
    try:
        state = None
        var_name = "Unknown"
        for v_name in ["__NUXT__", "__NEXT_DATA__", "__m_initial_state__"]:
            state = await p.evaluate(f"() => window.{v_name}")
            if state:
                var_name = f"{v_name} (Window)"
                break
        if not state:
            html_content = await p.content()
            nuxt_m = re.search(r'__NUXT__\s*=\s*(.*?);\s*</script>', html_content, re.DOTALL)
            if nuxt_m:
                js_code = nuxt_m.group(1)
                json_m = re.search(r'({.*})', js_code, re.DOTALL)
                if json_m:
                    try:
                        state = json.loads(json_m.group(1))
                        var_name = "Regex (Nuxt HTML)"
                    except: pass
        if not state: return

        data = {}
        if "NUXT" in var_name:
            nuxt_all = state.get("data", {})
            for key, val in nuxt_all.items():
                if isinstance(val, dict):
                    if val.get("data", {}).get("linkInfo"):
                        data = val.get("data", {})
                        break
                    if val.get("linkInfo"):
                        data = val
                        break
        if not data:
            props = state.get("props", {}).get("pageProps", {})
            data = props.get("info", {}).get("data", {}) or props.get("detail", {}).get("data", {})
        
        if not data: return
        link_info = data.get("linkInfo", {})
        house_info = data.get("houseInfo", data.get("ware", {})) or {}
        
        if s_data["email"] == "無":
            email = link_info.get("email") or data.get("email")
            if email: s_data["email"] = str(email)
        
        if s_data["api_phone"] == "無":
            aph = link_info.get("mobile") or link_info.get("phone") or \
                  link_info.get("ware_mobile") or data.get("mobile")
            if aph: 
                s_aph = str(aph).strip()
                if "0972528577" not in s_aph.replace("-", ""):
                    s_data["api_phone"] = s_aph
        
        remark = house_info.get("houseRemark") or house_info.get("remark") or ""
        if remark:
            f_info = []
            p_res = re.findall(r'09\d{2}-?\d{3}-?\d{3}', remark)
            if p_res: f_info.append(f"電話:{p_res[0]}")
            l_res = re.findall(r'(?:LINE|line|ID|id|賴|加賴|帳號|帳戶|++)\s?[:：]?\s?([a-zA-Z0-9._-]+)', remark)
            if l_res:
                clean = [m for m in l_res if len(m) > 2 and m not in ["房屋", "介紹", "歡迎"]]
                if clean: f_info.append(f"LINE:{clean[0]}")
            if f_info:
                s_data["remark_info"] = " | ".join(f_info)
    except: pass

async def extract_details():
    if not os.path.exists(CSV_FILE):
        print(f"[!] Error: Cannot find {CSV_FILE}, please run 1_rent.py first.")
        return

    try:
        df_pending = pd.read_csv(CSV_FILE)
    except:
        return
        
    if len(df_pending) == 0:
        return

    # --- [優化] 只從 Google Sheets 同步已有的案件ID ---
    existing_ids = set()
    sheets = SheetsHelper()
    if sheets.authenticated:
        cloud_ids = sheets.get_existing_keys("Rent", key_column_index=1)
        if cloud_ids:
            existing_ids = set(cloud_ids)
            print(f"[#] Synced Google Sheets data, total {len(existing_ids)} existing cases.")

    # --- [優化] 併發控制與資源攔截 ---
    sem = asyncio.Semaphore(3)  # 同時處理 3 個分頁
    save_lock = asyncio.Lock()

    async def fetch_one(context, url, index, total):
        async with sem:
            shared_data = {"email": "無", "api_phone": "無", "remark_info": "無", "address": "未知"}
            page = await context.new_page()
            
            async def block_resources(route):
                if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                    await route.abort()
                else:
                    await route.continue_()
            await page.route("**/*", block_resources)

            async def handle_response(response):
                url_res = response.url
                if ("v2/web/rent/detail" in url_res or "bff-house" in url_res) and ".html" not in url_res:
                    if response.status == 200:
                        try:
                            res_json = await response.json()
                            data = res_json.get("data", {})
                            if not data: return
                            info = data.get("houseInfo", data.get("ware", {}))
                            contact = data.get("linkInfo", data.get("contactInfo", {}))
                            email = info.get("email") or contact.get("email") or data.get("email")
                            if email: shared_data["email"] = str(email)
                            api_p = contact.get("mobile") or info.get("mobile") or \
                                    contact.get("phone") or contact.get("ware_mobile") or \
                                    info.get("phone") or data.get("mobile")
                            if api_p: shared_data["api_phone"] = str(api_p).strip()
                            if shared_data["address"] == "未知":
                                addr = info.get("address") or info.get("addr") or \
                                       data.get("address") or data.get("addr") or \
                                       info.get("fullAddress") or info.get("full_address")
                                if addr: shared_data["address"] = str(addr).strip()
                        except: pass
            
            page.on("response", handle_response)
            
            try:
                print(f"[*] [{index}/{total}] Processing: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                
                for _ in range(5):
                    if shared_data["api_phone"] != "無": break
                    await asyncio.sleep(0.5)
                
                if shared_data["api_phone"] == "無" or shared_data["email"] == "無":
                    await extract_from_bg_data(page, shared_data)

                # 抓取基本資訊
                title = "未知"
                for sel in [".house-title h1", "h1", ".detail-title-content"]:
                    if await page.locator(sel).count() > 0:
                        title = (await page.locator(sel).first.inner_text()).strip()
                        break
                
                price = "0"
                for sel in [".price strong", ".house-price"]:
                    if await page.locator(sel).count() > 0:
                        p_t = (await page.locator(sel).first.inner_text()).strip()
                        price = p_t.replace("買賣租屋風險，重點一次看懂!!", "").strip()
                        break

                address = shared_data["address"]
                if address == "未知":
                    try:
                        await page.wait_for_selector(".load-map", timeout=5000)
                    except: pass
                    for addr_sel in [".load-map", ".house-addr", ".info-addr", ".detail-address"]:
                        if await page.locator(addr_sel).count() > 0:
                            addr_text = (await page.locator(addr_sel).first.inner_text()).strip()
                            if addr_text:
                                address = addr_text
                                break

                owner = "未知"
                pot_locs = page.locator(".contact-info .name, .contact-card .name, section.contact .name")
                for i in range(await pot_locs.count()):
                    t = (await pot_locs.nth(i).inner_text()).strip()
                    if t and not any(tag in t for tag in ["交通", "生活", "捷運"]):
                        owner = t
                        break

                phone = "未獲取"
                if shared_data["api_phone"] != "無":
                    tmp_ph = shared_data["api_phone"]
                    if "0972528577" in tmp_ph.replace("-", ""): phone = "591電話"
                    else: phone = tmp_ph
                
                if (phone in ["未獲取", "591電話"]) and shared_data.get("remark_info") != "無":
                    match_rem = re.search(r'電話:(09[0-9-]+)', shared_data["remark_info"])
                    if match_rem: phone = match_rem.group(1)

                if phone in ["未獲取", "591電話"]:
                    try:
                        btns = page.locator("button:has-text('全部'), button:has-text('電話'), .t5-button--info")
                        if await btns.count() > 0:
                            await btns.first.click()
                            await asyncio.sleep(0.5)
                    except: pass
                    for s_loc in await page.locator("span:has-text('09'), a:has-text('09')").all():
                        txt_ph = await s_loc.inner_text()
                        m = re.search(r'(09\d{2}-\d{3}-\d{3}|09\d{8,})', str(txt_ph))
                        if m:
                            tmp_ph = str(m.group(1))
                            if "0972528577" in tmp_ph.replace("-", ""): phone = "591電話"
                            else:
                                phone = tmp_ph
                                break

                # Posted Time extraction
                posted_time_text = "Unknown"
                # For Rent, we can try several selectors
                for sel in [".publish-info", ".update-info", ".house-index span:has-text('更新')"]:
                    if await page.locator(sel).count() > 0:
                        txt = (await page.locator(sel).first.inner_text()).strip()
                        posted_time_text = SheetsHelper.parse_591_time(txt)
                        break

                match_cid = re.search(r'/(\d+)', url)
                curr_cid = match_cid.group(1) if match_cid else "未知"

                res = {
                    "案件ID": curr_cid,
                    "案件名稱": title,
                    "租金": price,
                    "地址": address.replace("地圖", "").replace("查看地圖", "").strip(),
                    "屋主/聯絡人": owner,
                    "電話": phone,
                    "網址": url,
                    "發佈時間": posted_time_text,
                    "抓取時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
                
                async with save_lock:
                    save_single(res, sheets)
                
                print(f"[+] Done: {title[:10]} | Price: {price} | Phone: {phone}")
                await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                print(f"[!] Error ({url}): {e}")
            finally:
                await page.close()

    async with async_playwright() as p:
        print(f"[*] Starting browser (headless mode)...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        all_urls = df_pending["url"].tolist()
        urls_to_process = []
        for u in all_urls:
            match = re.search(r'/(\d+)', str(u))
            if match:
                case_id = str(match.group(1))
                if case_id not in existing_ids or RE_SCRAPE_ALL:
                    urls_to_process.append(u)
        
        print(f"[*] Pending list: total {len(all_urls)}, remaining {len(urls_to_process)} to process.")
        if not urls_to_process:
            print("[*] No new cases to process.")
            await browser.close()
            return

        tasks = []
        for i, url in enumerate(urls_to_process):
            tasks.append(fetch_one(context, url, i + 1, len(urls_to_process)))
        
        await asyncio.gather(*tasks)
        await browser.close()

def save_single(item, sheets=None):
    if sheets and sheets.authenticated:
        sheets.sync_data("Rent", item)

if __name__ == "__main__":
    asyncio.run(extract_details())
