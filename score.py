import pandas as pd
import re

# EPS-tuned dictionaries
INDUSTRY_KEYWORDS = {
    "Chemicals": ["chemical", "chem", "specialty", "resin", "solvent", "polymer", "intermediate"],
    "Agrochemicals": ["agro", "fertilizer", "pesticide", "crop", "seed", "agro-chem"],
    "Food & Beverage": ["dairy", "brew", "beverage", "food", "distillery", "sugar", "edible oil", "brewery"],
    "Pharma": ["pharma", "biotech", "api", "formulation", "gmp", "cgmp"],
    "Oil & Gas": ["refinery", "petro", "oil", "gas", "downstream", "upstream", "offshore"],
    "General Manufacturing": ["manufacturing", "fabrication", "plant"]
}

PRODUCT_KEYWORDS = {
    "Vacuum Systems": ["vacuum", "dry pump", "liquid ring", "roots", "screw pump"],
    "Evaporation": ["evaporator", "mvr", "falling film", "forced circulation", "evaporation"],
    "Distillation": ["distillation", "rectification", "column", "vacuum distillation"],
    "Filtration": ["filter", "nutsch", "acg filter", "bag filter", "cartridge"],
    "Condensation": ["condenser", "condensation", "heat exchanger"],
    "Scrubbing": ["scrubber", "packed bed", "venturi", "caustic scrubber"]
}

REGION_HINTS = {
    "India": ["india", "mumbai", "pune", "gujarat", "hyderabad", "vizag", "visakhapatnam", "bengaluru", "delhi", "noida", ".in"],
    "Middle East": ["uae", "dubai", "abu dhabi", "saudi", "oman", "qatar", "bahrain", "kuwait", ".ae", ".sa", ".qa", ".om", ".bh", ".kw"],
    "SE Asia": ["indonesia", "jakarta", "malaysia", "kuala lumpur", "thailand", "vietnam", "philippines", "singapore", ".id", ".my", ".th", ".vn", ".ph", ".sg"],
    "South America": ["brazil", "argentina", "colombia", "chile", "peru", ".br", ".ar", ".co", ".cl", ".pe"],
    "Italy": ["italy", "italia", "milan", "torino", ".it"],
    "Bulgaria": ["bulgaria", "sofia", ".bg"],
    "Europe": ["germany", "france", "spain", "uk", "poland", "netherlands", ".de", ".fr", ".es", ".uk", ".pl", ".nl"],
    "North America": ["usa", "united states", "canada", "mexico", ".us", ".ca", ".mx"]
}

CUSTOMER_TYPES = {
    "EPC": ["epc", "engineering procurement", "turnkey", "lump sum", "integrator", "system integrator"],
    "OEM": ["oem", "original equipment manufacturer", "machine builder", "skid"],
    "End User": ["plant", "factory", "manufacturer", "processing", "production"],
    "Distributor": ["distributor", "channel partner", "reseller", "dealer"]
}

COMPETITORS = ["busch", "edwards", "atlas copco", "pfeiffer", "leybold", "ingersoll rand", "gardner denver"]

def _contains_any(text, keywords):
    t = str(text).lower()
    return any(k in t for k in keywords)

def score_leads(df: pd.DataFrame, industry_focus=None, regions=None, product_needs=None):
    df = df.copy()
    for col in ["lead_score","customer_type","priority_region","competitor_flag"]:
        if col not in df.columns: df[col] = None
    df["lead_score"] = 0

    # Base quality
    df["lead_score"] += df["email"].notna().astype(int) * 10
    df["lead_score"] += df["phone"].notna().astype(int) * 5
    df["lead_score"] += df["website"].notna().astype(int) * 5

    # Industry fit
    if industry_focus:
        for ind in industry_focus:
            kws = INDUSTRY_KEYWORDS.get(ind, [])
            df["lead_score"] += df.apply(
                lambda r: 15 if _contains_any(f"{r.get('industry','')} {r.get('notes','')}", kws) else 0,
                axis=1
            )

    # Product/process fit
    if product_needs:
        for p in product_needs:
            kws = PRODUCT_KEYWORDS.get(p, [])
            df["lead_score"] += df.apply(
                lambda r: 15 if _contains_any(f"{r.get('notes','')} {r.get('website','')}", kws) else 0,
                axis=1
            )

    # Region priority + priority_region tag
    def region_bonus(row):
        hay = f"{row.get('country','')} {row.get('state','')} {row.get('city','')} {row.get('email','')} {row.get('website','')}"
        for reg in regions or []:
            if _contains_any(hay, REGION_HINTS.get(reg, [])):
                row["priority_region"] = reg
                return 10
        return 0
    df["lead_score"] += df.apply(region_bonus, axis=1)

    # Customer type detect
    def detect_customer_type(row):
        hay = f"{row.get('industry','')} {row.get('job_title','')} {row.get('notes','')} {row.get('company_name','')}"
        for ctype, kws in CUSTOMER_TYPES.items():
            if _contains_any(hay, kws):
                return ctype
        return "Unknown"
    df["customer_type"] = df.apply(detect_customer_type, axis=1)

    # Decision-maker hint
    df["lead_score"] += df["contact_name"].fillna("").str.lower().str.contains(
        "director|manager|head|vp|chief|owner|ceo|cto|operations|procurement|maintenance|project"
    ).astype(int) * 10

    # Company vs free email
    df["lead_score"] += df["email"].fillna("").str.contains("@(gmail|yahoo|hotmail|outlook)\\.").apply(lambda x: -5 if x else 5)

    # Competitor penalty and flag
    def competitor_penalty(row):
        hay = f"{row.get('notes','')} {row.get('website','')} {row.get('company_name','')}"
        if _contains_any(hay, COMPETITORS):
            row["competitor_flag"] = True
            return -20
        row["competitor_flag"] = False
        return 0
    df["lead_score"] += df.apply(competitor_penalty, axis=1)

    df["lead_score"] = df["lead_score"].clip(0, 100)
    return df

def assign_lifecycle_stage(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    def stage(score):
        if score >= 80: return "salesqualifiedlead"
        if score >= 65: return "marketingqualifiedlead"
        return "lead"
    df["lifecycle_stage"] = df["lead_score"].apply(stage)
    return df
