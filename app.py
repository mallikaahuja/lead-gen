import os
import io
import pandas as pd
import streamlit as st
from datetime import datetime

from modules.score import score_leads, assign_lifecycle_stage
from modules.dedupe import dedupe_leads
from modules.export_hubspot import export_for_hubspot
from modules.utils import normalize_columns

from modules.extract_google import google_search_leads
from modules.extract_event import parse_event_file
from modules.extract_crm import parse_crm_export
from modules.extract_indiamart_local import parse_indiamart_files

st.set_page_config(page_title="EPS LeadGen (Extractors v2)", page_icon="🧲")

st.title("🧲 EPS Lead Generation — with Extractors")
st.caption("Add leads via: Google search, Event lists (Excel/PDF), CRM exports, or local IndiaMART pages (no API).")

with st.expander("CSV schema & tips"):
    st.markdown("""
    **Preferred columns (case-insensitive):**
    `company_name, contact_name, email, phone, website, country, state, city, industry, job_title, notes`
    """)

st.sidebar.header("Campaign Settings")
industry_focus = st.sidebar.multiselect(
    "Industry focus",
    ["Chemicals", "Agrochemicals", "Food & Beverage", "Pharma", "Oil & Gas", "General Manufacturing"],
    default=["Chemicals","Agrochemicals","Food & Beverage","Pharma","Oil & Gas"]
)
regions = st.sidebar.multiselect(
    "Priority regions",
    ["India", "Middle East", "SE Asia", "South America", "Italy", "Bulgaria", "Europe", "North America"],
    default=["India","Middle East","SE Asia","South America","Italy","Bulgaria"]
)
product_needs = st.sidebar.multiselect(
    "Product/Process focus",
    ["Vacuum Systems", "Evaporation", "Distillation", "Filtration", "Condensation", "Scrubbing"],
    default=["Vacuum Systems","Evaporation","Condensation","Distillation","Scrubbing"]
)
min_score = st.sidebar.slider("Minimum score to keep", 0, 100, 65)
lead_source = st.sidebar.selectbox("Lead Source", ["Indiamart", "Event", "Referral", "Inbound", "Outbound List", "Other"], index=0)

tabs = st.tabs(["Upload CSV", "Google Search", "Event List", "CRM Export", "IndiaMART (No API)"])

def process_and_display(df: pd.DataFrame, source_label: str):
    if df is None or df.empty:
        st.warning("No rows found from this extractor.")
        return None, None, None
    df = normalize_columns(df)
    st.subheader(f"Preview from {source_label}")
    st.dataframe(df.head(20))

    df = dedupe_leads(df)
    df_scored = score_leads(df, industry_focus=industry_focus, regions=regions, product_needs=product_needs)
    df_scored = assign_lifecycle_stage(df_scored)

    st.subheader("Scored + Lifecycle")
    st.dataframe(df_scored.head(20))
    keep = df_scored[df_scored["lead_score"] >= min_score].copy()
    st.metric("Leads above threshold", len(keep))
    hs = export_for_hubspot(keep, lead_source=lead_source)
    return df, df_scored, hs

# Upload CSV
with tabs[0]:
    up = st.file_uploader("Upload leads CSV", type=["csv"])
    if up:
        df = pd.read_csv(up)
        raw, scored, hs = process_and_display(df, "CSV Upload")
        if hs is not None:
            st.download_button("⬇️ HubSpot-ready CSV", hs.to_csv(index=False).encode("utf-8"),
                               file_name=f"hubspot_import_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                               mime="text/csv")

# Google Search
with tabs[1]:
    query = st.text_input("Query", "evaporator manufacturer site:.in")
    site_filter_im = st.checkbox("Restrict to IndiaMART (site:indiamart.com)", value=False)
    cse_key = st.text_input("CSE API Key (optional)", type="password")
    cse_id = st.text_input("CSE ID (optional)")
    max_results = st.number_input("Max results", 1, 50, 20)
    if st.button("Run Google Search"):
        df = google_search_leads(query, cse_key=cse_key or None, cse_id=cse_id or None,
                                 site_indiamart=site_filter_im, max_results=int(max_results))
        process_and_display(df, "Google Search")

# Event List
with tabs[2]:
    ev = st.file_uploader("Event file", type=["xlsx","xls","csv","pdf"])
    if ev:
        df = parse_event_file(ev)
        process_and_display(df, "Event List")

# CRM Export
with tabs[3]:
    crm = st.file_uploader("CRM export file", type=["xlsx","xls","csv"])
    if crm:
        df = parse_crm_export(crm)
        process_and_display(df, "CRM Export")

# IndiaMART (No API)
with tabs[4]:
    files = st.file_uploader("Upload IndiaMART files (HTML/CSV/XLS/XLSX)", type=["html","htm","csv","xls","xlsx"], accept_multiple_files=True)
    if files:
        df = parse_indiamart_files(files)
        process_and_display(df, "IndiaMART (No API)")
