import gspread
from google.oauth2.service_account import Credentials
import os
import json
import re
from datetime import datetime, timedelta
import pandas as pd

# 設定
SHEET_ID = "1LPw8RUYU-7qF2oiR1_hBmCdmm-YR5XJUwITRL_Jf_fA"
CREDENTIALS_FILE = "credentials.json"

class SheetsHelper:
    def __init__(self):
        self.gc = None
        self.sh = None
        self.authenticated = False
        self._authenticate()

    def _authenticate(self):
        # Priority 1: Check environment variable (for GitHub Actions)
        env_creds = os.getenv("GCP_CREDENTIALS")
        
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            if env_creds:
                # Load from JSON string in environment variable
                creds_dict = json.loads(env_creds)
                credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                print("[+] Using credentials from environment variable.")
            else:
                # Priority 2: Check local credentials.json
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"[!] Cannot find {CREDENTIALS_FILE} and GCP_CREDENTIALS env var is empty.")
                    return
                credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
                print(f"[+] Using credentials from {CREDENTIALS_FILE}.")

            self.gc = gspread.authorize(credentials)
            self.sh = self.gc.open_by_key(SHEET_ID)
            self.authenticated = True
        except Exception as e:
            print(f"[!] Google Sheets Authentication Failed: {e}")

    def sync_data(self, worksheet_name, data_dict):
        """
        Sync a single data record to the specified worksheet (Rent or Sale).
        """
        if not self.authenticated:
            return False

        try:
            # Get or create worksheet
            try:
                worksheet = self.sh.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.sh.add_worksheet(title=worksheet_name, rows=100, cols=20)
                # Write headers
                headers = list(data_dict.keys())
                worksheet.append_row(headers)

            # Note: Deduplication based on ID or URL can be added here for performance if needed.
            row_values = [str(val) for val in data_dict.values()]
            worksheet.insert_row(row_values, 2)
            return True
        except Exception as e:
            print(f"[!] Sync to Google Sheets failed ({worksheet_name}): {e}")
            return False

    def get_existing_keys(self, worksheet_name, key_column_index=1):
        """
        Get existing keys from the worksheet (used for deduplication).
        key_column_index: 1-based index
        """
        if not self.authenticated:
            return set()
        try:
            worksheet = self.sh.worksheet(worksheet_name)
            col_values = worksheet.col_values(key_column_index)
            return set(col_values[1:]) # Skip header
        except:
            return set()


    @staticmethod
    def parse_591_time(time_str):
        """
        Parses 591 relative time strings into absolute datetime strings.
        """
        if not time_str or not isinstance(time_str, str):
            return "Unknown"
            
        now = datetime.now()
        time_str = time_str.strip()
        
        try:
            # 1. Relative patterns
            m = re.search(r'(\d+)\s*(?:分鐘|min)', time_str)
            if m:
                return (now - timedelta(minutes=int(m.group(1)))).strftime("%Y-%m-%d %H:%M")
            
            m = re.search(r'(\d+)\s*(?:小時|hour)', time_str)
            if m:
                return (now - timedelta(hours=int(m.group(1)))).strftime("%Y-%m-%d %H:%M")
            
            m = re.search(r'(\d+)\s*(?:天|day)', time_str)
            if m:
                return (now - timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d %H:%M")
            
            if "昨日" in time_str or "昨天" in time_str:
                return (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")

            # 2. Date patterns (Month/Day)
            m = re.search(r'(\d+)\s*月\s*(\d+)\s*日', time_str)
            if m:
                month, day = int(m.group(1)), int(m.group(2))
                res_date = now.replace(month=month, day=day)
                if res_date > now:
                    res_date = res_date.replace(year=now.year - 1)
                return res_date.strftime("%Y-%m-%d") + " 00:00"

            m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', time_str)
            if m:
                return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d} 00:00"
            
            return time_str
        except Exception as e:
            return f"Error: {e}"
if __name__ == "__main__":
    # Test code
    helper = SheetsHelper()
    if helper.authenticated:
        print("[+] Authentication Successful!")
        test_data = {"Test": "Data", "Time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
        helper.sync_data("TestTab", test_data)
