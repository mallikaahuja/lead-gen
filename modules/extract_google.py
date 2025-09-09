
import os
import re
import time
from typing import Optional
import requests
import pandas as pd

def google_search_leads(query: str, cse_key: Optional[str]=None, cse_id: Optional[str]=None, site_indiamart: bool=False, max_results: int=20) -> pd.DataFrame:
    # Uses Google Programmable Search Engine if key+cx provided.
    # If not, falls back to a simple public results page scrape (brittle; for demo).
    q = query.strip()
    if site_indiamart and "site:" not in q:
        q = f"site:indiamart.com {q}"
    items = []

    if cse_key and cse_id:
        start = 1
        while len(items) < max_results:
            params = {"key": cse_key, "cx": cse_id, "q": q, "start": start}
            r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=15)
            if r.status_code != 200:
                break
            js = r.json()
            batch = js.get("items", [])
            if not batch:
                break
            items.extend(batch)
            start += 10
            time.sleep(0.2)
        rows = []
        for it in items[:max_results]:
            url = it.get("link") or it.get("formattedUrl") or ""
            title = it.get("title") or it.get("htmlTitle") or ""
            snippet = it.get("snippet") or ""
            rows.append({
                "company_name": None,
                "contact_name": None,
                "email": None,
                "phone": None,
                "website": url,
                "country": None,
                "state": None,
                "city": None,
                "industry": None,
                "job_title": None,
                "notes": f"google:{title} | {snippet}".strip()
            })
        return pd.DataFrame(rows)
    else:
        params = {"q": q}
        r = requests.get("https://www.google.com/search", params=params, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        urls = []
        if r.status_code == 200:
            urls = re.findall(r'href="/url\\?q=(https?://[^"&]+)', r.text)
        rows = [{
            "company_name": None,
            "contact_name": None,
            "email": None,
            "phone": None,
            "website": u,
            "country": None,
            "state": None,
            "city": None,
            "industry": None,
            "job_title": None,
            "notes": "google_fallback"
        } for u in urls[:max_results]]
        return pd.DataFrame(rows)
