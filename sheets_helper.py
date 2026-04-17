import gspread
from google.oauth2.service_account import Credentials
import os
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
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"⚠️ 找不到 {CREDENTIALS_FILE}，請參考教學文件設定。")
            return

        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            self.gc = gspread.authorize(credentials)
            self.sh = self.gc.open_by_key(SHEET_ID)
            self.authenticated = True
        except Exception as e:
            print(f"❌ Google Sheets 驗證失敗: {e}")

    def sync_data(self, worksheet_name, data_dict):
        """
        將單筆資料同步至指定的工作表 (租屋或售屋)
        """
        if not self.authenticated:
            return False

        try:
            # 取得或建立工作表
            try:
                worksheet = self.sh.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.sh.add_worksheet(title=worksheet_name, rows=100, cols=20)
                # 寫入標頭
                headers = list(data_dict.keys())
                worksheet.append_row(headers)

            # 檢查是否已有相同 ID (如果是租屋) 或 網址 (如果是售屋)
            # 讀取現有資料的第一欄位作為 Key (假設 租屋是 案件ID, 售屋是 案件名稱或網址)
            # 為了效能，我們這裡先簡單使用 append_row
            # 如果需要去重，可以在這裡增加邏輯
            
            row_values = [str(val) for val in data_dict.values()]
            worksheet.append_row(row_values)
            return True
        except Exception as e:
            print(f"❌ 同步至 Google Sheets 失敗 ({worksheet_name}): {e}")
            return False

    def get_existing_keys(self, worksheet_name, key_column_index=1):
        """
        取得現有資料中的 Key (用於去重)
        key_column_index: 1-based index
        """
        if not self.authenticated:
            return set()
        try:
            worksheet = self.sh.worksheet(worksheet_name)
            col_values = worksheet.col_values(key_column_index)
            return set(col_values[1:]) # 排除標頭
        except:
            return set()

if __name__ == "__main__":
    # 測試程式碼
    helper = SheetsHelper()
    if helper.authenticated:
        print("✅ 驗證成功！")
        test_data = {"測試": "資料", "時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
        helper.sync_data("測試用", test_data)
