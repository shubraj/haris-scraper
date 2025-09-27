import streamlit as st
import pandas as pd
import json
from datetime import date
from .logic import scrape_instruments


def run_app1():
    st.title("Instrument Scraper")

    # Load instrument types from JSON
    with open("instrument_types.json", "r", encoding="utf-8") as f:
        instrument_types = json.load(f)

    # --- User Inputs ---
    instrument_keys = st.multiselect(
        "Select Instrument Types",
        sorted(set(instrument_types.keys()))
    )

    start_date = st.date_input("Start Date", value=date(2025, 9, 1))
    end_date = st.date_input("End Date", value=date(2025, 9, 10))

    final_df = None  # default return value

    # --- Run Button ---
    if st.button("Start Scraping") and instrument_keys:
        final_df = scrape_instruments(instrument_keys, instrument_types, start_date, end_date)

        if final_df is not None and not final_df.empty:
            st.success("✅ Scraping completed!")
            st.write("### Results")
            st.dataframe(final_df)
        else:
            st.info("No data found for selected instrument types.")

    return final_df  # <<-- return DataFrame (or None)
