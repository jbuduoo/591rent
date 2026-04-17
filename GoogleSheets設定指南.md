# Google Sheets API 設定教學

為了讓租屋爬蟲能夠自動將資料寫入您的 Google Sheets，請按照以下步驟建立金鑰：

### 第一步：建立 Google Cloud 專案
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。
2. 點擊左上角的專案選擇器，選擇 **「建立專案 (New Project)」**，命名為 `591-Scraper`。
3. 在上方搜尋列搜尋 **「Google Sheets API」** 並點擊 **「啟用 (Enable)」**。
4. 搜尋 **「Google Drive API」** 並點擊 **「啟用 (Enable)」**。

### 第二步：建立服務帳戶 (Service Account)
1. 前往 **「導覽選單 > API 和服務 > 憑證 (Credentials)」**。
2. 點擊 **「建立憑證 (Create Credentials)」**，選擇 **「服務帳戶 (Service Account)」**。
3. 輸入服務帳戶名稱（例如：`scraper-bot`），點擊 **「建立並繼續」**。
4. **角色 (Role)** 選擇：`基本 > 編輯者 (Editor)`，然後點擊 **「完成」**。

### 第三步：產生金鑰檔案 (JSON)
1. 在憑證頁面下方的「服務帳戶」列表中，點擊剛建立的帳戶。
2. 切換到 **「金鑰 (Keys)」** 頁籤。
3. 點擊 **「新增金鑰 > 建立新金鑰」**。
4. 選擇 **「JSON」** 格式，點擊 **「建立」**。
5. **重要：** 瀏覽器會自動下載一個 `.json` 檔案。請將該檔案重新命名為 `credentials.json`，並放入您的專案資料夾中：
   `c:\Users\wits\Documents\程式專區\01_591_20260325\591租屋_git版\credentials.json`

### 第四步：共用試算表權限
1. 打開您的 `credentials.json` 檔案，尋找 `"client_email"` 欄位，它看起來像 `scraper-bot@...iam.gserviceaccount.com`。
2. 複製這個電子郵件地址。
3. 前往您的 [Google 試算表連結](https://docs.google.com/spreadsheets/d/1LPw8RUYU-7qF2oiR1_hBmCdmm-YR5XJUwITRL_Jf_fA/edit?usp=sharing)。
4. 點擊右上角 **「共用 (Share)」**。
5. 將剛才複製的電郵地址貼上去，並給予 **「編輯者 (Editor)」** 權限，取消勾選「通知」，點擊 **「傳送」**。

---
完成以上步驟後，請跟我說一聲，我將為您部署自動同步的代碼！
