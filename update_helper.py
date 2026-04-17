import os

def update_sheets_helper():
    path = 'sheets_helper.py'
    if not os.path.exists(path):
        print(f"Skipping {path}")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    imports_added = False
    method_added = False
    
    for line in lines:
        if 'import json' in line and not imports_added:
            new_lines.append(line)
            new_lines.append('import re\n')
            new_lines.append('from datetime import datetime, timedelta\n')
            imports_added = True
            continue
        
        if 'if __name__ == "__main__":' in line and not method_added:
            # Add the method before the main block
            new_lines.append('\n')
            new_lines.append('    @staticmethod\n')
            new_lines.append('    def parse_591_time(time_str):\n')
            new_lines.append('        """\n')
            new_lines.append('        Parses 591 relative time strings into absolute datetime strings.\n')
            new_lines.append('        """\n')
            new_lines.append('        if not time_str or not isinstance(time_str, str):\n')
            new_lines.append('            return "Unknown"\n')
            new_lines.append('            \n')
            new_lines.append('        now = datetime.now()\n')
            new_lines.append('        time_str = time_str.strip()\n')
            new_lines.append('        \n')
            new_lines.append('        try:\n')
            new_lines.append('            # 1. Relative patterns\n')
            new_lines.append(r"            m = re.search(r'(\d+)\s*(?:分鐘|min)', time_str)")
            new_lines.append('\n            if m:\n')
            new_lines.append('                return (now - timedelta(minutes=int(m.group(1)))).strftime("%Y-%m-%d %H:%M")\n')
            new_lines.append('            \n')
            new_lines.append(r"            m = re.search(r'(\d+)\s*(?:小時|hour)', time_str)")
            new_lines.append('\n            if m:\n')
            new_lines.append('                return (now - timedelta(hours=int(m.group(1)))).strftime("%Y-%m-%d %H:%M")\n')
            new_lines.append('            \n')
            new_lines.append(r"            m = re.search(r'(\d+)\s*(?:天|day)', time_str)")
            new_lines.append('\n            if m:\n')
            new_lines.append('                return (now - timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d %H:%M")\n')
            new_lines.append('            \n')
            new_lines.append('            if "昨日" in time_str or "昨天" in time_str:\n')
            new_lines.append('                return (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")\n')
            new_lines.append('\n')
            new_lines.append('            # 2. Date patterns (Month/Day)\n')
            new_lines.append(r"            m = re.search(r'(\d+)\s*月\s*(\d+)\s*日', time_str)")
            new_lines.append('\n            if m:\n')
            new_lines.append('                month, day = int(m.group(1)), int(m.group(2))\n')
            new_lines.append('                res_date = now.replace(month=month, day=day)\n')
            new_lines.append('                if res_date > now:\n')
            new_lines.append('                    res_date = res_date.replace(year=now.year - 1)\n')
            new_lines.append('                return res_date.strftime("%Y-%m-%d") + " 00:00"\n')
            new_lines.append('\n')
            new_lines.append(r"            m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', time_str)")
            new_lines.append('\n            if m:\n')
            new_lines.append('                return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d} 00:00"\n')
            new_lines.append('            \n')
            new_lines.append('            return time_str\n')
            new_lines.append('        except Exception as e:\n')
            new_lines.append('            return f"Error: {e}"\n')
            
            new_lines.append(line)
            method_added = True
            continue
            
        new_lines.append(line)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully modified {path}")

if __name__ == "__main__":
    update_sheets_helper()
