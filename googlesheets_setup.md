# Google Sheets 雲端同步設定指南

本爬蟲支援將抓取到的 591 租屋與售屋資料自動同步到 Google Sheets，方便您在任何地方查看。

## 設定步驟

### 1. 建立 Google Cloud 專案
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。
2. 建立一個新專案，名稱可取為 `591-Scraper`。
3. 搜尋並啟用以下兩個 API：
   - **Google Sheets API**
   - **Google Drive API**

### 2. 建立服務帳戶 (Service Account)
1. 在「API 和服務」中點擊「憑證」。
2. 點擊「建立憑證」 > 「服務帳戶」。
3. 完成建立後，在該帳戶的「金鑰」分頁中，點擊「新增金鑰」 > 「建立新金鑰」 > 選擇 **JSON**。
4. 下載下來的 JSON 檔案請重新命名為 **`credentials.json`**，並放在本專案的根目錄。

### 3. 共用試算表
1. 建立一個新的 Google 試算表，或是打開現有的。
2. 複製試算表網址中的 ID（在 `/d/` 之後那一串字元）。
3. 打開 `sheets_helper.py`，將 `SHEET_ID` 修改為您的試算表 ID。
4. **重要**：點擊試算表右上角的「共用」按鈕，將您的**服務帳戶 Email**（在 `credentials.json` 裡面可以找到）加入為「編輯者」。

## 自動化欄位說明
- **Rent 分頁**：存放租屋資料。
- **Sale 分頁**：存放售屋資料。
- 程式會自動偵測標題，若偵測到已存在的「案件ID」，則會跳過重複抓取。

---
**安全性提示**：`credentials.json` 包含金鑰，請務必妥善保存，切勿將其上傳至公開的 GitHub 倉庫。
 Riverside 37
