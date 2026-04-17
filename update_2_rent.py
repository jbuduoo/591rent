import os

def update_2_rent():
    path = '2_rent.py'
    if not os.path.exists(path):
        print(f"Skipping {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Extraction logic
    extraction_block = """
                # Posted Time extraction
                posted_time_text = "Unknown"
                publish_info_loc = page.locator(".publish-info")
                if await publish_info_loc.count() > 0:
                    posted_time_raw = (await publish_info_loc.first.inner_text()).strip()
                    # Example: "此房屋在14天前發佈 (2小時內更新)"
                    # We want the "14天前" or "4月2日" part
                    m = re.search(r'在(.*?)(?:發佈|刊登)', posted_time_raw)
                    if m:
                        posted_time_text = SheetsHelper.parse_591_time(m.group(1))
                    else:
                        posted_time_text = SheetsHelper.parse_591_time(posted_time_raw)
"""
    
    # 2. Res dictionary update
    old_res = """                res = {
                    "案件ID": curr_cid,
                    "案件名稱": title,
                    "租金": price,
                    "地址": address.replace("地圖", "").replace("查看地圖", "").strip(),
                    "屋主/聯絡人": owner,
                    "電話": phone,
                    "網址": url,
                    "最後更新日": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }"""
                
    new_res = """                res = {
                    "案件ID": curr_cid,
                    "案件名稱": title,
                    "租金": price,
                    "地址": address.replace("地圖", "").replace("查看地圖", "").strip(),
                    "屋主/聯絡人": owner,
                    "電話": phone,
                    "網址": url,
                    "發佈時間": posted_time_text,
                    "抓取時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }"""

    if 'owner = "未知"' in content:
        content = content.replace('owner = "未知"', extraction_block + '                owner = "未知"')
    
    if old_res in content:
        content = content.replace(old_res, new_res)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully modified {path}")

if __name__ == "__main__":
    update_2_rent()
 Riverside
