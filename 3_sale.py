import asyncio
import os
import re
import random
from playwright.async_api import async_playwright

# 售案設定
TARGET_URL = "https://sale.591.com.tw/?regionid=3&section=38,37&shType=host"
CSV_FILE = "pending_sale_urls.csv"
PAGE_LOG = "3_sale_page_log.txt"

async def fetch_sale_urls(pages=8): # 範圍給大一點，靠自動停止來結束
    # 1. 初始化檔案
    print(f"🧹 正在清空 {CSV_FILE} 並建立 {PAGE_LOG}...")
    with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
        f.write("url\n")
    
    with open(PAGE_LOG, "w", encoding="utf-8") as f:
        f.write("=== 591 售屋 點擊式分頁 (帶自動停止功能) ===\n\n")
    
    all_found_set = set() 

    async with async_playwright() as p:
        print(f"💡 啟動瀏覽器中...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # 先進入初始頁面
        print(f"🌐 正在進入初始頁面: {TARGET_URL}")
        await page.goto(TARGET_URL, wait_until="load", timeout=90000)
        await asyncio.sleep(5)

        for p_idx in range(pages):
            try:
                print(f"\n📄 [第 {p_idx + 1} 頁] 正在加載與掃描內容...")
                
                # --- 真人慢慢捲動 ---
                for _ in range(6):
                    await page.mouse.wheel(0, 1000)
                    await asyncio.sleep(1.5)
                
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(4)

                # 抓取連結
                links = await page.locator("a[href*='/house/detail/']").all()
                total_links = len(links)
                
                with open(PAGE_LOG, "a", encoding="utf-8") as log_f:
                    log_f.write(f"\n--- 第 {p_idx + 1} 頁 ---\n")
                    log_f.write(f"當前 URL: {page.url}\n")
                    
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
                                log_f.write(f"[新] {full_url}\n")
                                with open(CSV_FILE, "a", encoding="utf-8-sig") as f:
                                    f.write(f"{full_url}\n")
                    
                    log_f.write(f"統計：新增 {page_new_count} 筆。\n")
                    print(f"✅ 第 {p_idx + 1} 頁完成，新增 {page_new_count} 筆 (區域連結共 {total_links} 筆)。")

                # --- 自動停止判斷 ---
                if page_new_count == 0:
                    print(f"🏁 本頁未發現任何新案子，判斷已全部抓取完畢，提早結束任務。")
                    break

                # 嘗試點擊「下一頁」
                if p_idx < pages - 1:
                    next_btn = page.locator("a.pageNext, .pageNext, .page-next, a:has-text('下一頁')").first
                    if await next_btn.is_visible():
                        print(f"👉 點擊「下一頁」開關載入更多...")
                        await next_btn.scroll_into_view_if_needed()
                        await next_btn.click()
                        await asyncio.sleep(8)
                    else:
                        print(f"🏁 已無「下一頁」按鈕，任務結束。")
                        break
                
            except Exception as e:
                print(f"💥 發生錯誤: {e}")
                break

        print(f"\n🚀 任務結束。總共存入 {len(all_found_set)} 筆售案網址。")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_sale_urls())
