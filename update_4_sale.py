import os
import re

def update_4_sale():
    path = '4_sale.py'
    if not os.path.exists(path):
        print(f"Skipping {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Extraction logic
    extraction_block = """
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
"""
    
    # 2. Results dictionary update
    new_results = """                    results = {
                        "案件名稱": title, "總價": price, "單價": unit_price,
                        "格局": layout, "坪數": area, "屋齡": age, "樓層": floor,
                        "社區": community, "地址": address, "屋主/聯絡人": owner,
                        "身分": role, "電話": phone, "網址": url,
                        "發佈時間": posted_time_text,
                        "抓取時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    }"""

    if 'results = {' in content:
        content = content.replace('results = {', extraction_block + '                    results = {')
    
    pattern = r'results = \{.*?抓取時間".*?\}'
    content = re.sub(pattern, new_results, content, flags=re.DOTALL)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully modified {path}")

if __name__ == "__main__":
    update_4_sale()
