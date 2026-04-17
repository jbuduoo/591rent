# 591 Scraper Project

This project crawls rental and sales data from 591.com.tw and syncs it to Google Sheets and local Excel files.

## Files

- `run_scraper.bat`: Double-click this to start the scraper.
- `install.bat`: Run this if you need to reinstall the environment (Python, .venv, etc.).
- `googlesheets_setup.md`: Guide to setting up Google Sheets integration.
- `credentials.json`: Your Google Service Account key (do not share).

## How to use

1. Ensure `python` is installed.
2. Ensure `credentials.json` is in this folder.
3. Double-click `run_scraper.bat`.

## Data storage

- **Google Sheets**: Data is saved to your configured sheet in tabs named **"Rent"** and **"Sale"**.
- **Excel**: Local backups are saved to `591_rentals.xlsx` and `591_sales.xlsx`.
