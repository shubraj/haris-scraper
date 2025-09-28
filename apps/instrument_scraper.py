"""
Instrument scraper application module.
"""
import streamlit as st
import pandas as pd
import json
from datetime import date
from typing import Optional, Dict, Any

from scrapers.harris_county_scraper import get_scraper
from config import INSTRUMENT_TYPES_FILE
from utils.logger_config import get_app_logger

# Configure logging
logger = get_app_logger()


class InstrumentScraperApp:
    """Streamlit application for scraping Harris County instrument data."""
    
    def __init__(self):
        self.instrument_types = self._load_instrument_types()
    
    def _load_instrument_types(self) -> Dict[str, str]:
        """Load instrument types from JSON file."""
        try:
            logger.info(f"Loading instrument types from {INSTRUMENT_TYPES_FILE}")
            with open(INSTRUMENT_TYPES_FILE, "r", encoding="utf-8") as f:
                types = json.load(f)
            logger.info(f"Successfully loaded {len(types)} instrument types")
            return types
        except FileNotFoundError:
            logger.error(f"Instrument types file not found: {INSTRUMENT_TYPES_FILE}")
            st.error(f"Instrument types file not found: {INSTRUMENT_TYPES_FILE}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing instrument types file: {e}")
            st.error(f"Error parsing instrument types file: {e}")
            return {}
    
    def run(self) -> Optional[pd.DataFrame]:
        """
        Run the instrument scraper application.
        
        Returns:
            DataFrame with scraped data or None if no data
        """
        st.title("Instrument Scraper")
        
        if not self.instrument_types:
            st.error("No instrument types available. Please check the configuration.")
            return None
        
        # User Inputs
        instrument_keys = st.multiselect(
            "Select Instrument Types",
            sorted(set(self.instrument_types.keys())),
            help="Select one or more instrument types to scrape"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date", 
                value=date(2025, 9, 1),
                help="Start date for the search range"
            )
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=date(2025, 9, 10),
                help="End date for the search range"
            )
        
        # Validation
        if start_date > end_date:
            st.error("Start date must be before end date.")
            return None
        
        final_df = None
        
        # Run Button
        if st.button("Start Scraping", type="primary") and instrument_keys:
            logger.info(f"Starting scraping for {len(instrument_keys)} instrument types: {instrument_keys}")
            with st.spinner("Scraping instrument data..."):
                # Group keys by code (avoid scraping duplicates)
                code_to_keys = {}
                for key in instrument_keys:
                    code = self.instrument_types[key]
                    code_to_keys.setdefault(code, []).append(key)
                
                logger.info(f"Grouped into {len(code_to_keys)} unique codes to scrape")
                all_results = []
                progress_bar = st.progress(0)
                total_codes = len(code_to_keys)
                
                for i, (code, keys) in enumerate(code_to_keys.items()):
                    logger.info(f"Scraping code {code} for keys: {keys}")
                    st.write(f"Scraping: {', '.join(keys)} (Code: {code})")
                    
                    df = get_scraper().scrape_records(code, start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y"))
                    if not df.empty:
                        df["Instrument Type"] = ", ".join(keys)
                        all_results.append(df)
                        logger.info(f"Successfully scraped {len(df)} records for code {code}")
                        st.success(f"Found {len(df)} records")
                    else:
                        logger.warning(f"No data found for code {code}")
                        st.info("No data found for this instrument type")
                    
                    progress_bar.progress((i + 1) / total_codes)
                
                if all_results:
                    final_df = pd.concat(all_results, ignore_index=True)
                    st.success(f"✅ Scraping completed! Total records: {len(final_df)}")
                    
                    # Display results
                    st.write("### Results")
                    st.dataframe(final_df)
                    
                    # Download button
                    csv = final_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"instrument_data_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No data found for selected instrument types.")
        
        return final_df


def run_app1() -> Optional[pd.DataFrame]:
    """
    Convenience function to run the instrument scraper app.
    
    Returns:
        DataFrame with scraped data or None
    """
    app = InstrumentScraperApp()
    return app.run()
