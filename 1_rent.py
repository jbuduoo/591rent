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
    # 1. 初始化：清空 CSV 並寫入標題 (使用 utf-8-sig 以便 Excel 讀取)
    print(f"🧹 正在清空 {CSV_FILE} 並準備開始新任務...")
    with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
        f.write("url\n")
    
    all_found_set = set() # 用來記錄本次任務中已抓到的網址，防止重複

    async with async_playwright() as p:
        print(f"💡 正在啟動瀏覽器，準備針對 {len(TARGET_URLS)} 個網址進行抓取...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for u_idx, target_url in enumerate(TARGET_URLS):
            print(f"\n📂 [網址 {u_idx + 1}/{len(TARGET_URLS)}] 開始處理地區網址...")
            
            for p_idx in range(pages):
                first_row = p_idx * 30
                current_page_url = f"{target_url}&firstRow={first_row}"
                
                try:
                    print(f"🌐 [{p_idx + 1}/{pages}] 正在獲取: {current_page_url}", flush=True)
                    await page.goto(current_page_url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(5)
                    
                    # 滾動一下確保載入
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
                                
                                # 如果是新發現的
                                if full_url not in all_found_set:
                                    all_found_set.add(full_url)
                                    page_found_count += 1
                                    
                                    # --- 讀取一筆就 Log 一筆，也寫入一筆 ---
                                    print(f"  ✨ 發現新連結 [{page_found_count}]: {full_url}", flush=True)
                                    try:
                                        with open(CSV_FILE, "a", encoding="utf-8-sig") as f:
                                            f.write(f"{full_url}\n")
                                    except PermissionError:
                                        print(f"  ⚠️ 警告: 無法寫入檔案，請關閉正在預覽的 Excel！")
                    
                    print(f"✅ 第 {p_idx + 1} 頁處理完成，新增 {page_found_count} 筆。")
                    
                    if page_found_count == 0:
                        print(f"🏁 此網址已無更多新連結，換下一個或結束。")
                        break

                    await asyncio.sleep(random.uniform(2, 4))

                except Exception as e:
                    print(f"💥 第 {p_idx + 1} 頁發生錯誤: {e}")
                    break

        print(f"\n🚀 所有任務結束。本次共抓取 {len(all_found_set)} 筆網址並存入 {CSV_FILE}。")
        await browser.close()



if __name__ == "__main__":
    asyncio.run(fetch_urls())
