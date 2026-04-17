import os
import re

def clean_script(path, worksheet_name, key_col_idx):
    if not os.path.exists(path):
        print(f"Skipping {path}")
        return
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove EXCEL_FILE definition
    content = re.sub(r'EXCEL_FILE = ".*?"\n', '', content)
    
    # 2. Update existing data loading logic
    # Find the block where existing data is loaded
    if 'extract_details' in content or 'extract_sale_details' in content:
        # Replacement for Rent
        if "Rent" in content:
            new_load = f"""
    # --- [優化] 只從 Google Sheets 同步已有的案件ID ---
    existing_ids = set()
    sheets = SheetsHelper()
    if sheets.authenticated:
        cloud_ids = sheets.get_existing_keys("{worksheet_name}", key_column_index={key_col_idx})
        if cloud_ids:
            existing_ids = set(cloud_ids)
            print(f"[#] Synced Google Sheets data, total {{len(existing_ids)}} existing cases.")
"""
            # Replace the old blocks (Excel + Sheets combination)
            # Find the section between "定義電話標準化函數" and "# --- [優化] 併發控制"
            pattern = re.compile(r'# 讀取現有的資料庫.*?# --- \[New\] Initialize Google Sheets Helper ---.*?# ---------------------------------------------', re.DOTALL)
            content = pattern.sub(new_load, content)
            
            # Special case for rent where it used existing_phones too (just remove the phone check part)
            content = content.replace('if norm_curr in existing_phones: phone = f"{phone}已有"', '')
            content = content.replace('else: existing_phones.add(norm_curr)', '')
        
        # Replacement for Sale
        elif "Sale" in content:
            new_load = f"""
    # --- [優化] 只從 Google Sheets 同步已有的網址 ---
    existing_urls = set()
    sheets = SheetsHelper()
    if sheets.authenticated:
        cloud_urls = sheets.get_existing_keys("{worksheet_name}", key_column_index={key_col_idx})
        if cloud_urls:
            existing_urls = set(cloud_urls)
            print(f"[#] Synced Google Sheets data, total {{len(existing_urls)}} existing URLs.")
"""
            pattern = re.compile(r'# --- \[新增\] 讀取現有資料庫.*?# --- \[New\] Initialize Google Sheets Helper ---.*?# ---------------------------------------------', re.DOTALL)
            content = content.sub(new_load) if hasattr(content, 'sub') else content # safety
            # If regex match fails, do fallback
            if '# --- [新增] 讀取現有資料庫' in content:
                # Find the whole section manually
                start_marker = '# --- [新增] 讀取現有資料庫'
                end_marker = '# ---------------------------------------------'
                start_idx = content.find(start_marker)
                end_idx = content.find(end_marker, start_idx) + len(end_marker)
                if start_idx != -1 and end_idx != -1:
                    content = content[:start_idx] + new_load + content[end_idx:]

    # 3. Simplify save_single
    new_save_single = f"""
def save_single(item, sheets=None):
    # Only Sync to Google Sheets
    if sheets and sheets.authenticated:
        sheets.sync_data("{worksheet_name}", item)
"""
    # Capture the old save_single function
    content = re.sub(r'def save_single\(item, file_path, sheets=None\):.*?if __name__ == "__main__":', new_save_single + '\n\nif __name__ == "__main__":', content, flags=re.DOTALL)
    
    # 4. Update calls to save_single
    content = content.replace('save_single(res, EXCEL_FILE, sheets)', 'save_single(res, sheets)')
    content = content.replace('save_single(results, EXCEL_FILE, sheets)', 'save_single(results, sheets)')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully cleaned local Excel logic from {path}")

if __name__ == "__main__":
    # Rent: ID is Col 1
    clean_script('2_rent.py', 'Rent', 1)
    # Sale: URL is Col 14
    clean_script('4_sale.py', 'Sale', 14)
