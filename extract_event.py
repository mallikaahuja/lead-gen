
import pandas as pd
import pdfplumber

def parse_event_file(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith((".xlsx",".xls",".csv")):
        if name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        df.columns = [c.strip() for c in df.columns]
        colmap = {
            "company":"company_name",
            "organization":"company_name",
            "organisation":"company_name",
            "name":"contact_name",
            "contact":"contact_name",
            "email":"email",
            "mail":"email",
            "phone":"phone",
            "mobile":"phone",
            "website":"website",
            "city":"city",
            "state":"state",
            "country":"country",
            "title":"job_title",
            "designation":"job_title",
            "industry":"industry"
        }
        for c in list(df.columns):
            key = c.strip().lower()
            if key in colmap:
                df.rename(columns={c:colmap[key]}, inplace=True)
        for r in ["company_name","contact_name","email","phone","website","country","state","city","industry","job_title","notes"]:
            if r not in df.columns: df[r] = None
        df["notes"] = df.get("notes","").fillna("") + " | source=event_list"
        return df[["company_name","contact_name","email","phone","website","country","state","city","industry","job_title","notes"]]
    elif name.endswith(".pdf"):
        rows = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for line in text.split("\\n"):
                    if len(line.strip()) < 5: continue
                    rows.append({"notes": f"event_pdf:{line.strip()}"})
        df = pd.DataFrame(rows)
        for r in ["company_name","contact_name","email","phone","website","country","state","city","industry","job_title"]:
            if r not in df.columns: df[r] = None
        return df[["company_name","contact_name","email","phone","website","country","state","city","industry","job_title","notes"]]
    else:
        return pd.DataFrame()
