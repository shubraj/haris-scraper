"""
HCAD property search application module.
"""
import streamlit as st
import pandas as pd
import asyncio
from typing import Optional

from scrapers.hcad import run_hcad_searches


class HCADSearchApp:
    """Streamlit application for HCAD property searches."""
    
    def run(self, df: Optional[pd.DataFrame]) -> None:
        """
        Run the HCAD search application.
        
        Args:
            df: DataFrame with instrument data from the scraper
        """
        st.title("HCAD Property Search")
        
        if df is None or df.empty:
            st.warning("No input data available. Please run the instrument scraper first.")
            return
        
        st.write("### Input Data (from Instrument Scraper)")
        st.dataframe(df)
        
        # Display summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Unique Grantees", df['Grantees'].nunique() if 'Grantees' in df.columns else 0)
        with col3:
            st.metric("Records with Legal Description", 
                     df['LegalDescription'].notna().sum() if 'LegalDescription' in df.columns else 0)
        
        # Initialize state
        if "hcad_running" not in st.session_state:
            st.session_state.hcad_running = False
        
        # Search controls
        st.write("### HCAD Search Controls")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Run HCAD Searches", 
                        disabled=st.session_state.hcad_running,
                        type="primary"):
                st.session_state.hcad_running = True
        with col2:
            if st.button("Reset Search", disabled=st.session_state.hcad_running):
                st.session_state.hcad_running = False
                st.rerun()
        
        # Display search progress and results
        if st.session_state.hcad_running:
            st.info("🔍 Running HCAD searches... This may take several minutes.")
            
            # Create placeholder for results
            results_placeholder = st.empty()
            
            try:
                # Run the searches
                asyncio.run(run_hcad_searches(df, results_placeholder))
                st.success("✅ HCAD searches completed!")
                st.session_state.hcad_running = False
                
                # Show final results
                if 'hcad_results' in st.session_state:
                    final_df = st.session_state.hcad_results
                    st.write("### Final Results")
                    st.dataframe(final_df)
                    
                    # Download results
                    csv = final_df.to_csv(index=False)
                    st.download_button(
                        label="Download Results CSV",
                        data=csv,
                        file_name="hcad_search_results.csv",
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"Error during HCAD search: {e}")
                st.session_state.hcad_running = False
        else:
            st.info("Click 'Run HCAD Searches' to start the property search process.")


def run_app2(df: Optional[pd.DataFrame]) -> None:
    """
    Convenience function to run the HCAD search app.
    
    Args:
        df: DataFrame with instrument data from the scraper
    """
    app = HCADSearchApp()
    app.run(df)
