
import pandas as pd

def parse_crm_export(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    df.columns = [c.strip() for c in df.columns]
    colmap = {
        "account":"company_name",
        "company":"company_name",
        "name":"contact_name",
        "contact":"contact_name",
        "email":"email",
        "mail":"email",
        "phone":"phone",
        "mobile":"phone",
        "website":"website",
        "url":"website",
        "city":"city",
        "state":"state",
        "country":"country",
        "title":"job_title",
        "designation":"job_title",
        "industry":"industry",
        "notes":"notes",
        "description":"notes"
    }
    for c in list(df.columns):
        key = c.strip().lower()
        if key in colmap:
            df.rename(columns={c:colmap[key]}, inplace=True)
    for r in ["company_name","contact_name","email","phone","website","country","state","city","industry","job_title","notes"]:
        if r not in df.columns: df[r] = None
    df["notes"] = df.get("notes","").fillna("") + " | source=crm_export"
    return df[["company_name","contact_name","email","phone","website","country","state","city","industry","job_title","notes"]]
