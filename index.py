import pandas as pd
import requests
import whois
from datetime import datetime
import pytz

CST = pytz.timezone("America/Chicago")

def is_website_active(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def convert_to_cst(dt):
    """Convert datetime(s) or string(s) to CST and remove timezone info."""
    if isinstance(dt, list):
        for d in dt:
            converted = convert_to_cst(d)
            if converted:
                return converted
        return None

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
        return {
            "registrar": w.registrar,
            "creation_date": convert_to_cst(w.creation_date),
            "expiration_date": convert_to_cst(w.expiration_date),
            "updated_date": convert_to_cst(w.updated_date)
        }
    except Exception as e:
        return {"error": str(e)}

def check_websites(websites):
    results = []
    for site in websites:
        domain = site.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"🔍 Checking {site} ...")

        active = is_website_active(site)
        info = get_domain_info(domain)

        results.append({
            "Website": site,
            "Active": active,
            "Registrar": info.get("registrar"),
            "Created (CST)": info.get("creation_date"),
            "Expires (CST)": info.get("expiration_date"),
            "Updated (CST)": info.get("updated_date"),
            "Error": info.get("error")
        })
    return results

websites = [
    "https://openai.com",
    "https://secre-vvccentro.com"
]

data = check_websites(websites)

df = pd.DataFrame(data)
df.to_excel("website_check_results.xlsx", index=False)

print("✅ Results saved to website_check_results.xlsx (CST timezone)")
