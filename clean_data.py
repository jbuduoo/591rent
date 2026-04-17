import gspread
from google.oauth2.service_account import Credentials
import os
import pandas as pd
import json

SHEET_ID = "1LPw8RUYU-7qF2oiR1_hBmCdmm-YR5XJUwITRL_Jf_fA"
CREDENTIALS_FILE = "credentials.json"
TARGET_STRING = "買賣租屋風險，重點一次看懂!!"

def clean_cloud():
    print("[*] Starting Cloud Data Cleaning...")
    
    # Auth
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    env_creds = os.getenv("GCP_CREDENTIALS")
    if env_creds:
        credentials = Credentials.from_service_account_info(json.loads(env_creds), scopes=scopes)
    else:
        # Check if local credentials file exists
        if not os.path.exists(CREDENTIALS_FILE):
             print(f"[!] Error: {CREDENTIALS_FILE} not found. Please setup credentials first.")
             return
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SHEET_ID)
    
    # Find active tabs
    worksheets = sh.worksheets()
    for ws in worksheets:
        name = ws.title
        if name in ["Rent", "租屋"]:
            print(f"[*] Cleaning Worksheet: {name}")
            data = ws.get_all_values()
            if not data: continue
            
            headers = data[0]
            try:
                price_col_index = headers.index("租金") + 1
                print(f"    - Found '租金' column at index {price_col_index}")
            except ValueError:
                print(f"    - Could not find '租金' column in {name}")
                continue
                
            # Get all values from that column to identify rows to fix
            col_values = ws.col_values(price_col_index)
            updates = []
            for i, val in enumerate(col_values):
                if TARGET_STRING in val:
                    new_val = val.replace(TARGET_STRING, "").strip()
                    # index i is 0-based row, worksheet cell is 1-based
                    # Row i+1, Col price_col_index
                    cell_a1 = gspread.utils.rowcol_to_a1(i + 1, price_col_index)
                    updates.append({
                        'range': cell_a1,
                        'values': [[new_val]]
                    })
            
            if updates:
                print(f"    - Found {len(updates)} rows to clean in {name}. Updating...")
                # Batch update for efficiency
                ws.batch_update(updates)
                print(f"    - Successfully cleaned {name}.")
            else:
                print(f"    - No cleaning needed for {name}.")

def clean_local():
    excel_path = "591_rentals.xlsx"
    if os.path.exists(excel_path):
        print(f"[*] Cleaning Local File: {excel_path}")
        try:
            df = pd.read_excel(excel_path)
            if "租金" in df.columns:
                count_before = df["租金"].astype(str).str.contains(TARGET_STRING).sum()
                df["租金"] = df["租金"].astype(str).str.replace(TARGET_STRING, "", regex=False).str.strip()
                df.to_excel(excel_path, index=False)
                print(f"    - Cleaned {count_before} rows in local Excel.")
            else:
                print(f"    - '租金' column not found in {excel_path}.")
        except Exception as e:
            print(f"    - Error cleaning local file: {e}")

if __name__ == "__main__":
    clean_cloud()
    clean_local()
    print("[*] All Cleaning Tasks Finished.")
