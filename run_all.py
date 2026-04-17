import subprocess
import sys
import os

def run_script(script_name, description):
    print(f"\n{'='*52}")
    print(f"  🚀 {description}")
    print(f"{'='*52}\n")
    
    result = subprocess.run([sys.executable, script_name], check=False)
    
    if result.returncode == 0:
        print(f"\n  ✅ {description} — 完成！")
    else:
        print(f"\n  ❌ {description} — 發生錯誤，停止執行。")
        input("\n  請按 Enter 鍵結束，並將畫面截圖給技術人員...")
        sys.exit(1)

if __name__ == "__main__":
    # 確保切換到腳本所在的目錄（讓相對路徑的 CSV / Excel 都能正確找到）
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        run_script("1_rent.py", "步驟 1/4：租屋網址蒐集")
        run_script("2_rent.py", "步驟 2/4：租屋詳細資訊擷取")
        run_script("3_sale.py", "步驟 3/4：售屋網址蒐集")
        run_script("4_sale.py", "步驟 4/4：售屋詳細資訊擷取")

        print(f"\n{'='*52}")
        print("  🎉 所有任務全部完成！")
        print("  資料已更新至：")
        print("    - 591_rentals.xlsx（租屋資料）")
        print("    - 591_sales.xlsx  （售屋資料）")
        print(f"{'='*52}\n")
    
    except KeyboardInterrupt:
        print("\n\n  ⚠️  使用者手動中斷執行。")
    except Exception as e:
        print(f"\n  💥 發生非預期錯誤：{e}")

    input("\n  按 Enter 鍵關閉視窗...")
