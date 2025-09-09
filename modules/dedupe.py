
import pandas as pd

def dedupe_leads(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["company_name","email","website"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()
    df["has_email"] = df["email"].notna() & df["email"].str.contains("@")
    df["has_website"] = df["website"].notna() & df["website"].str.contains("\.")
    df["row_rank"] = df["has_email"].astype(int)*2 + df["has_website"].astype(int)
    df_sorted = df.sort_values(by=["company_name","row_rank"], ascending=[True, False])
    deduped = df_sorted.drop_duplicates(subset=["company_name","email"], keep="first")
    return deduped.drop(columns=["has_email","has_website","row_rank"], errors="ignore")
