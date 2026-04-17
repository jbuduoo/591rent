# GitHub Actions 自動化執行設定指南

透過此設定，程式將會每天早上 08:00 自動在雲端執行爬蟲，並將資料同步至您的 Google Sheets。

## 設定步驟

### 1. 複製金鑰內容
- 打開您電腦中的 `credentials.json`。
- **全選並複製** 裡面的所有內容（是一段 JSON 文字）。

### 2. 在 GitHub 設定 Secret
1. 前往您的 GitHub 專案頁面。
2. 點擊上方的 **Settings** 標籤。
3. 在左側選單中尋找 **Secrets and variables** > **Actions**。
4. 點擊右側的 **New repository secret** 按鈕。
5. **Name** 輸入：`GCP_CREDENTIALS`
6. **Secret** 貼上您剛才複製的 JSON 內容。
7. 點擊 **Add secret**。

### 3. 開啟與測試
1. 點擊 GitHub 上方的 **Actions** 標籤。
2. 在左側點擊 **Daily 591 Scraper**。
3. 如果出現黃色提示，請點擊 **Enable workflow**（通常第一次需要開啟）。
4. 若要手動測試，點擊右側的 **Run workflow** 下拉選單，再次點擊綠色的 **Run workflow**。

---

## 注意事項
- **定時任務**：我已經設定為每天早上 08:00 (台北時間) 執行。
- **免登入**：雲端執行時不需要您的電腦保持開啟。
- **分頁名稱**：雲端同步會使用英文分頁名稱（`Rent` / `Sale`）。

設定完成後，您可以前往 **Actions** 頁面觀察執行進度。如果顯示綠色勾勾，代表雲端同步已成功！
 Riverside
