import os

def modify_2_rent():
    path = '2_rent.py'
    if not os.path.exists(path):
        print(f"Skipping {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add filtering logic
    old_line = 'price = (await page.locator(sel).first.inner_text()).strip()'
    new_line = 'price = (await page.locator(sel).first.inner_text()).strip()\n                        # [Filter] Remove unwanted text\n                        price = price.replace("買賣租屋風險，重點一次看懂!!", "").strip()'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully modified {path}")
    else:
        print(f"Could not find target line in {path}")

def modify_sheets_helper():
    path = 'sheets_helper.py'
    if not os.path.exists(path):
        print(f"Skipping {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    import_json_added = False
    auth_replaced = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Add import json
        if 'import os' in line and not import_json_added:
            new_lines.append(line)
            new_lines.append('import json\n')
            import_json_added = True
            i += 1
            continue
            
        # Replace _authenticate method
        if 'def _authenticate(self):' in line and not auth_replaced:
            new_lines.append(line)
            new_lines.append('        # Priority 1: Check environment variable (for GitHub Actions)\n')
            new_lines.append('        env_creds = os.getenv("GCP_CREDENTIALS")\n')
            new_lines.append('        \n')
            new_lines.append('        try:\n')
            new_lines.append('            scopes = [\n')
            new_lines.append("                'https://www.googleapis.com/auth/spreadsheets',\n")
            new_lines.append("                'https://www.googleapis.com/auth/drive'\n")
            new_lines.append('            ]\n')
            new_lines.append('            \n')
            new_lines.append('            if env_creds:\n')
            new_lines.append('                # Load from JSON string in environment variable\n')
            new_lines.append('                creds_dict = json.loads(env_creds)\n')
            new_lines.append('                credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)\n')
            new_lines.append('                print("[+] Using credentials from environment variable.")\n')
            new_lines.append('            else:\n')
            new_lines.append('                # Priority 2: Check local credentials.json\n')
            new_lines.append('                if not os.path.exists(CREDENTIALS_FILE):\n')
            new_lines.append('                    print(f"[!] Cannot find {CREDENTIALS_FILE} and GCP_CREDENTIALS env var is empty.")\n')
            new_lines.append('                    return\n')
            new_lines.append('                credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)\n')
            new_lines.append(f'                print(f"[+] Using credentials from {{CREDENTIALS_FILE}}.")\n')
            new_lines.append('\n')
            new_lines.append('            self.gc = gspread.authorize(credentials)\n')
            new_lines.append('            self.sh = self.gc.open_by_key(SHEET_ID)\n')
            new_lines.append('            self.authenticated = True\n')
            new_lines.append('        except Exception as e:\n')
            new_lines.append('            print(f"[!] Google Sheets Authentication Failed: {e}")\n')
            
            # Skip the old block
            while i < len(lines) and 'self.authenticated = True' not in lines[i]:
                i += 1
            # Skip the catch block if any (up to next method or end of function)
            while i < len(lines) and 'def ' not in lines[i] and 'if __name__' not in lines[i]:
                if 'print(f"[!] Google Sheets Authentication Failed' in lines[i]:
                    i += 1
                    break
                i += 1
            auth_replaced = True
            continue
            
        new_lines.append(line)
        i += 1
        
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully modified {path}")

if __name__ == "__main__":
    modify_2_rent()
    modify_sheets_helper()
