import time
import random
import re
import argparse
from datetime import datetime
from playwright.sync_api import sync_playwright
from sheets_helper import SheetsHelper

# 設定
REGIONS = ["中和", "永和", "土城", "板橋", "新店", "新莊", "三重"]
WORKSHEET_NAME = "FB屋主自租"
SEARCH_INTERVAL_HOURS = 3
HEADLESS = False # 開啟瀏覽器模式，方便遇到驗證碼時手動點擊

def parse_time_from_snippet(text):
    """
    從 Google 搜尋摘要中提取時間資訊。
    """
    if not text:
        return ""
    
    patterns = [
        r'(\d+\s*(?:分鐘|小時|天)前)',
        r'(\d+月\d+日)',
        r'(昨天|今天)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
            
    return ""

def check_captcha(page):
    """
    偵測是否有驗證碼，如果有則停下來等待使用者處理。
    """
    if "google.com/sorry" in page.url or "captcha" in page.content().lower():
        print("\n" + "!"*50)
        print("[!] 偵測到 Google 驗證碼 (CAPTCHA)！")
        print("[!] 請在跳出的瀏覽器視窗中手動完成驗證。")
        print("[!] 處理完後，程式將自動繼續執行...")
        print("!"*50 + "\n")
        
        # 等待驗證碼消失
        while "google.com/sorry" in page.url or "captcha" in page.content().lower():
            time.sleep(2)
        
        print("[+] 驗證已完成，繼續執行任務...")
        time.sleep(2)
        return True
    return False

def scrape_google(page, region):
    print(f"[+] 正在搜尋區域: {region}...")
    # 稍微修改搜尋詞，使其更自然
    query = f'facebook {region} "屋主自租"'
    search_url = f"https://www.google.com/search?q={query}&tbs=qdr:w"
    
    results = []
    try:
        # 隱藏自動化特徵
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(random.uniform(2, 4))
        
        # 檢查驗證碼
        check_captcha(page)

        # 檢查是否有搜尋結果
        if page.locator("#res, #search").count() == 0:
            print(f"[-] {region} 無搜尋結果或被封鎖。")
            return results

        # 抓取搜尋結果容器
        items = page.locator("div.g, .MjjYud, .MjjYxb").all()
        
        for item in items:
            try:
                # 提取連結，只抓 Facebook 的贴文
                link_elem = item.locator("a[href*='facebook.com']").first
                if not link_elem.count():
                    continue
                    
                url_at = link_elem.get_attribute("href")
                if not url_at or "google.com" in url_at:
                    continue

                # 提取摘要與時間
                snippet_elem = item.locator("div.VwiC3b, .yBF84b").first
                snippet_text = snippet_elem.inner_text() if snippet_elem.count() else ""
                
                post_time = parse_time_from_snippet(snippet_text)
                if not post_time:
                    post_time = "一週內"
                
                results.append({
                    "刊登時間": post_time,
                    "網址": url_at,
                    "關鍵字": region
                })
            except Exception:
                continue
                
    except Exception as e:
        print(f"[!] 搜尋 {region} 時發生錯誤: {e}")
        
    print(f"[OK] {region} 抓取到 {len(results)} 筆結果。")
    return results

def run_task():
    print(f"\n{'-'*50}")
    print(f"[*] 開始執行 FB 爬蟲任務 (Google 版) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'-'*50}")
    
    helper = SheetsHelper()
    if not helper.authenticated:
        print("[!] Google Sheets 認證失敗。")
        return

    existing_urls = helper.get_existing_keys(WORKSHEET_NAME, key_column_index=2)
    print(f"[*] 目前試算表中已有 {len(existing_urls)} 筆網址。")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            extra_http_headers={
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )
        
        page = context.new_page()
        
        new_items_count = 0
        for region in REGIONS:
            results = scrape_google(page, region)
            
            for item in results:
                # 簡單清理 URL
                clean_url = item["網址"].split("?")[0].rstrip("/")
                if clean_url not in existing_urls:
                    success = helper.sync_data(WORKSHEET_NAME, item)
                    if success:
                        existing_urls.add(clean_url)
                        new_items_count += 1
                        print(f"    [NEW] 已同步: {clean_url} ({item['刊登時間']})")
                
            time.sleep(random.uniform(5, 10))
            
        browser.close()
        
    print(f"\n[DONE] 任務完成。新增 {new_items_count} 筆資料。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Rental Scraper via Google Search")
    parser.add_argument("--once", action="store_true", help="執行一次後結束")
    args = parser.parse_args()

    if args.once:
        run_task()
    else:
        while True:
            try:
                run_task()
                print(f"\n[*] 任務結束。進入休眠，{SEARCH_INTERVAL_HOURS} 小時後再次執行...")
                time.sleep(SEARCH_INTERVAL_HOURS * 3600)
            except KeyboardInterrupt:
                print("\n[!] 程式已被使用者停止。")
                break
            except Exception as e:
                print(f"\n[!] 發生非預期錯誤: {e}")
                print("[*] 60 秒後嘗試重啟...")
                time.sleep(60)
