import os
import time
import requests
import pandas as pd

HUBSPOT_BASE = "https://api.hubapi.com"

def _headers():
    token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
    if not token:
        raise RuntimeError("HUBSPOT_PRIVATE_APP_TOKEN not set")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def _create_or_get_company(domain: str, name: str):
    headers = _headers()
    # Try search by domain if present
    if domain:
        # Search endpoint (simple)
        r = requests.get(f"{HUBSPOT_BASE}/crm/v3/objects/companies", headers=headers, params={"limit":1, "properties":"domain", "q":domain})
        if r.status_code == 200 and r.json().get("results"):
            return r.json()["results"][0]["id"]
    # Create
    payload = {"properties": {"domain": domain or "", "name": name or ""}}
    r = requests.post(f"{HUBSPOT_BASE}/crm/v3/objects/companies", headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["id"]

def _create_or_update_contact(row: pd.Series, company_id=None):
    headers = _headers()
    email = (row.get("email") or "").strip()
    props = {
        "email": email,
        "firstname": row.get("firstname") or "",
        "lastname": row.get("lastname") or "",
        "phone": row.get("phone") or "",
        "jobtitle": row.get("jobtitle") or "",
        "lifecyclestage": row.get("lifecyclestage") or "lead",
        "website": row.get("website") or "",
        "city": row.get("city") or "",
        "state": row.get("state") or "",
        "country": row.get("country") or "",
        "industry": row.get("industry") or "",
        "lead_source": row.get("lead_source") or "",
        "priority_region": row.get("priority_region") or "",
        "competitor_flag": str(row.get("competitor_flag") or ""),
        "notes": row.get("notes") or "",
        "lead_score": int(row.get("lead_score") or 0)
    }

    # Upsert by email (if provided)
    if email:
        # Try simple list endpoint with ?email=
        sr = requests.get(f"{HUBSPOT_BASE}/crm/v3/objects/contacts", headers=headers, params={"limit":1, "properties":"email", "q":email})
        if sr.status_code == 200 and sr.json().get("results"):
            cid = sr.json()["results"][0]["id"]
            ur = requests.patch(f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{cid}", headers=headers, json={"properties": props})
            ur.raise_for_status()
        else:
            cr = requests.post(f"{HUBSPOT_BASE}/crm/v3/objects/contacts", headers=headers, json={"properties": props})
            cr.raise_for_status()
            cid = cr.json()["id"]
    else:
        cr = requests.post(f"{HUBSPOT_BASE}/crm/v3/objects/contacts", headers=headers, json={"properties": props})
        cr.raise_for_status()
        cid = cr.json()["id"]

    # Associate with company
    if company_id:
        try:
            # Associations v3 (simple)
            assoc = requests.put(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{cid}/associations/companies/{company_id}/contact_to_company",
                headers=headers
            )
        except Exception:
            pass

    return cid

def sync_dataframe_to_hubspot(hs_df: pd.DataFrame) -> dict:
    contacts_created = 0
    companies_created = 0
    for _, row in hs_df.iterrows():
        company = (row.get("company") or "").strip()
        website = (row.get("website") or "").strip()
        # crude domain extraction
        domain = ""
        if website:
            w = website.replace("http://","").replace("https://","")
            domain = w.split("/",1)[0]

        company_id = None
        if company or domain:
            try:
                company_id = _create_or_get_company(domain, company or domain)
                companies_created += 1
            except Exception:
                pass

        _ = _create_or_update_contact(row, company_id=company_id)
        contacts_created += 1
        time.sleep(0.2)  # polite pacing

    return {"contacts_created": contacts_created, "companies_created": companies_created}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync a HubSpot-ready CSV to HubSpot via Private App token.")
    parser.add_argument("csv_path", help="Path to hubspot export CSV")
    args = parser.parse_args()
    df = pd.read_csv(args.csv_path)
    res = sync_dataframe_to_hubspot(df)
    print(res)
