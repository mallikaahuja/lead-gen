
import pandas as pd

def export_for_hubspot(df: pd.DataFrame, lead_source: str = "Indiamart") -> pd.DataFrame:
    out = pd.DataFrame()
    out["company"] = df.get("company_name", "")
    names = df.get("contact_name","").fillna("").str.split(" ", n=1, expand=True)
    out["firstname"] = names[0]
    out["lastname"] = names[1] if names.shape[1] > 1 else ""
    out["email"] = df.get("email","")
    out["phone"] = df.get("phone","")
    out["website"] = df.get("website","")
    out["city"] = df.get("city","")
    out["state"] = df.get("state","")
    out["country"] = df.get("country","")
    out["jobtitle"] = df.get("job_title","")
    out["industry"] = df.get("industry","")
    out["lifecyclestage"] = df.get("lifecycle_stage","lead")
    out["lead_source"] = lead_source
    out["priority_region"] = df.get("priority_region","")
    out["competitor_flag"] = df.get("competitor_flag", False).astype(str)
    out["lead_score"] = df.get("lead_score",0)
    out["notes"] = df.get("notes","")
    return out
