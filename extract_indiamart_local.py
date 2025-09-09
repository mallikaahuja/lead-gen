
from bs4 import BeautifulSoup
import pandas as pd

def _parse_html(file_bytes: bytes):
    soup = BeautifulSoup(file_bytes, "lxml")
    rows = []
    cards = soup.select("[class*=prod] , [class*=card] , [class*=cmpny] , [class*=supplier]")
    if not cards:
        cards = soup.find_all("a")
    for el in cards:
        text = el.get_text(" ", strip=True)
        link = el.get("href") or ""
        if not text: continue
        rows.append({
            "company_name": None,
            "contact_name": None,
            "email": None,
            "phone": None,
            "website": link if link and link.startswith("http") else None,
            "country": "India",
            "state": None,
            "city": None,
            "industry": None,
            "job_title": None,
            "notes": f"indiamart_html:{text[:140]}"
        })
    return pd.DataFrame(rows)

def parse_indiamart_files(files) -> pd.DataFrame:
    frames = []
    for file in files:
        name = file.name.lower()
        if name.endswith((".html",".htm")):
            content = file.read()
            frames.append(_parse_html(content))
        elif name.endswith(".csv"):
            frames.append(pd.read_csv(file))
        elif name.endswith((".xls",".xlsx")):
            frames.append(pd.read_excel(file))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True).drop_duplicates()
    for r in ["company_name","contact_name","email","phone","website","country","state","city","industry","job_title","notes"]:
        if r not in df.columns: df[r] = None
    df["notes"] = df.get("notes","").fillna("") + " | source=indiamart_local"
    return df[["company_name","contact_name","email","phone","website","country","state","city","industry","job_title","notes"]]
