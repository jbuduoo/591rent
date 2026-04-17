# Google Sheets API Setup Guide

To allow the scraper to write data to your Google Sheets, follow these steps to create a key:

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project selector in the top-left, select **"New Project"**, and name it `591-Scraper`.
3. In the search bar, search for **"Google Sheets API"** and click **"Enable"**.
4. Search for **"Google Drive API"** and click **"Enable"**.

### Step 2: Create a Service Account
1. Go to **"Navigation Menu > APIs & Services > Credentials"**.
2. Click **"Create Credentials"**, choose **"Service Account"**.
3. Name it (e.g., `scraper-bot`), and click **"Create and Continue"**.
4. Select **Role**: `Basic > Editor`, then click **"Done"**.

### Step 3: Generate JSON Key
1. In the "Service Accounts" list, click the account you just created.
2. Go to the **"Keys"** tab.
3. Click **"Add Key > Create New Key"**.
4. Select **"JSON"**, and click **"Create"**.
5. **Important:** Download the `.json` file, rename it to `credentials.json`, and place it in the project folder:
   `c:\Users\wits\Documents\程式專區\01_591_20260325\591租屋_git版\credentials.json`

### Step 4: Share your Spreadsheet
1. Open your `credentials.json` file and copy the `"client_email"` (e.g., `scraper-bot@...iam.gserviceaccount.com`).
2. Go to your [Google Sheets Link](https://docs.google.com/spreadsheets/d/1LPw8RUYU-7qF2oiR1_hBmCdmm-YR5XJUwITRL_Jf_fA/edit?usp=sharing).
3. Click **"Share"** in the top-right.
4. Paste the email address, give **"Editor"** permission, and click **"Send"**.

### Data Tabs
The scraper will automatically create or use tabs named **"Rent"** and **"Sale"** (English).

---
Once completed, you can run `run_scraper.bat` to start!
 Riverside
