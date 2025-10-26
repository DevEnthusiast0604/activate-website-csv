import pandas as pd
import requests
import whois
from datetime import datetime
import pytz
import time

CST = pytz.timezone("America/Chicago")

def is_website_active(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
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

# Pair complaint number and website, dropping rows where website is NaN
websites = df_input[["Complaint Number", "Websites"]].dropna(subset=["Websites"]).values.tolist()
data = check_websites(websites)

timestamp = datetime.now(CST).strftime("%Y-%m-%d_%H-%M")
output_file = f"website_check_results_{timestamp}.xlsx"

df = pd.DataFrame(data)
df.to_excel(output_file, index=False)

print(f"\n✅ Results saved to {output_file} (CST timezone)")
print("ℹ️ Note: WHOIS only shows current registrar info. Historical registrar data requires paid services like DomainTools or WhoisXML.")
