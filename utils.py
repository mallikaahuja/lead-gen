
import pandas as pd

COL_MAP = {
    "company": "company_name",
    "companyname": "company_name",
    "name": "contact_name",
    "contact": "contact_name",
    "mail": "email",
    "e-mail": "email",
    "phone number": "phone",
    "mobile": "phone",
    "site": "website",
    "url": "website",
    "state/province": "state",
    "province": "state",
    "job": "job_title",
    "title": "job_title"
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df.rename(columns={k:v for k,v in COL_MAP.items() if k in df.columns}, inplace=True)
    required = ["company_name","contact_name","email","phone","website","country","state","city","industry","notes","job_title"]
    for r in required:
        if r not in df.columns:
            df[r] = None
    return df
