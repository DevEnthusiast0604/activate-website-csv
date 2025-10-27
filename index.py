import pandas as pd
import requests
import whois
from datetime import datetime
import pytz
import time

CST = pytz.timezone("America/Chicago")

def is_website_active(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"\nDebug for {url}:")
        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed: Status code {response.status_code}")
            return False
            
        content_type = response.headers.get('content-type', '').lower()
        print(f"Content-Type: {content_type}")
        if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
            print("❌ Failed: Not HTML content")
            return False
            
        content = response.text.lower()
        print(f"Content Length: {len(content)} characters")
        
        if len(content) < 100:
            print("❌ Failed: Content too short")
            return False
            
        parking_indicators = [
            'domain is for sale',
            'buy this domain',
            'parked domain',
            'domain parking',
            'this website is for sale',
            '404 not found',
            'page not found',
            'website coming soon',
            'under construction',
            'error page',
            'site suspended',
            'account suspended'
        ]
        
        for indicator in parking_indicators:
            if indicator in content:
                print(f"❌ Failed: Found parking indicator: {indicator}")
                return False
                
        basic_html_elements = ['<html', '<body', '<head']
        if not any(element in content for element in basic_html_elements):
            print("❌ Failed: No basic HTML structure")
            return False
            
        print("✅ Website is active!")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Failed: Request error - {str(e)}")
        return False

def convert_to_cst(dt):
    if isinstance(dt, list):
        valid_dates = [convert_to_cst(d) for d in dt if convert_to_cst(d)]
        return min(valid_dates) if valid_dates else None

    if isinstance(dt, str):
        try:
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            return convert_to_cst(parsed)
        except Exception:
            return None

    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            dt = dt.astimezone(CST).replace(tzinfo=None)
        return dt
    return None

def get_domain_info(domain):
    try:
        w = whois.whois(domain)

        privacy_enabled = None
        if w.emails:
            privacy_enabled = any("privacy" in str(email).lower() or "protect" in str(email).lower() for email in w.emails)

        return {
            "registrar": w.registrar,
            "creation_date": convert_to_cst(w.creation_date),
            "expiration_date": convert_to_cst(w.expiration_date),
            "updated_date": convert_to_cst(w.updated_date),
            "privacy_enabled": privacy_enabled,
            "whois_server": w.whois_server
        }
    except Exception as e:
        return {
            "registrar": None,
            "creation_date": None,
            "expiration_date": None,
            "updated_date": None,
            "privacy_enabled": None,
            "whois_server": None,
            "error": str(e).split("\n")[0]
        }

def check_websites(websites):
    results = []
    for entry in websites:
        complaint_number = entry[0]
        site = entry[1]
        domain = site.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"🔍 Checking {site} ...")

        active = is_website_active(site)
        info = get_domain_info(domain)

        results.append({
            "Complaint Number": complaint_number,
            "Website": site,
            "Domain": domain,
            "Active": active,
            "Registrar": info.get("registrar"),
            "Privacy Enabled": info.get("privacy_enabled"),
            "WHOIS Server": info.get("whois_server"),
            "Created (CST)": info.get("creation_date"),
            "Expires (CST)": info.get("expiration_date"),
            "Updated (CST)": info.get("updated_date"),
            "Checked (CST)": datetime.now(CST).replace(tzinfo=None),
            "Error": info.get("error")
        })
        time.sleep(1)
    return results

input_file = "websites.xlsx"

if input_file.endswith(".xlsx"):
    temp_df = pd.read_excel(input_file, header=None)
    
    header_row = None
    for idx, row in temp_df.iterrows():
        if 'Websites' in [str(cell).strip() for cell in row.values]:
            header_row = idx
            break
    
    if header_row is None:
        raise ValueError("❌ Could not find a row containing 'Websites' column")
    
    df_input = pd.read_excel(input_file, header=header_row)
    print(f"\nFound headers at row {header_row + 1}")
    print("Available columns:", df_input.columns.tolist())
elif input_file.endswith(".csv"):
    df_input = pd.read_csv(input_file)
else:
    raise ValueError("❌ Please provide a .xlsx or .csv file")


print("Available columns:", df_input.columns.tolist())
if "Websites" not in df_input.columns or "Complaint Number" not in df_input.columns:
    raise ValueError("❌ Input file must have columns named 'Complaint Number' and 'Websites'")

websites = df_input[["Complaint Number", "Websites"]].dropna(subset=["Websites"]).values.tolist()
data = check_websites(websites)

timestamp = datetime.now(CST).strftime("%Y-%m-%d_%H-%M")
output_file = f"website_check_results_{timestamp}.xlsx"

df = pd.DataFrame(data)
df.to_excel(output_file, index=False)

print(f"\n✅ Results saved to {output_file} (CST timezone)")
print("ℹ️ Note: WHOIS only shows current registrar info. Historical registrar data requires paid services like DomainTools or WhoisXML.")
