import subprocess
import sys
import os

def run_script(script_name, description):
    print(f"\n{'='*52}")
    print(f"  >>> {description}")
    print(f"{'='*52}\n")
    
    result = subprocess.run([sys.executable, script_name], check=False)
    
    if result.returncode == 0:
        print(f"\n  [OK] {description} - Done!")
    else:
        print(f"\n  [ERROR] {description} - Failed.")
        input("\n  請按 Enter 鍵結束，並將畫面截圖給技術人員...")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure the working directory is set to the script's location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        run_script("1_rent.py", "Step 1/4: Rent URL Collection")
        run_script("2_rent.py", "Step 2/4: Rent Details Extraction")
        run_script("3_sale.py", "Step 3/4: Sale URL Collection")
        run_script("4_sale.py", "Step 4/4: Sale Details Extraction")

        print(f"\n{'='*52}")
        print("  [Finished] All tasks completed!")
        print("  Data updated to:")
        print("    - 591_rentals.xlsx (Rent data)")
        print("    - 591_sales.xlsx   (Sale data)")
        print(f"{'='*52}\n")
    
    except KeyboardInterrupt:
        print("\n\n  ⚠️  使用者手動中斷執行。")
    except Exception as e:
        print(f"\n  💥 發生非預期錯誤：{e}")

    input("\n  按 Enter 鍵關閉視窗...")
