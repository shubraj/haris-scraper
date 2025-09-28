"""
Harris County Property Scraper - Main Application

A comprehensive tool for scraping Harris County instrument data and performing
HCAD property searches.
"""
import streamlit as st
import os
from apps.instrument_scraper import run_app1
from apps.pdf_address_extractor import run_app2_pdf
from apps.hcad_search import run_app2_hcad

# Install Playwright
os.system("playwright install")

def main():
    """Main application entry point."""
    # Set page config
    st.set_page_config(
        page_title="Harris County Property Scraper",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar navigation
    st.sidebar.title("🏠 Harris County Property Scraper")
    st.sidebar.markdown("---")
    
    choice = st.sidebar.radio(
        "Select Step:",
        ["Step 1: Scrape Instruments", "Step 2: Extract PDF Addresses", "Step 3: HCAD Search"],
        help="Step 1: Scrape instrument data from Harris County records\nStep 2: Extract addresses from PDFs using AI\nStep 3: Search for property addresses using HCAD"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    This tool helps you:
    1. **Scrape** Harris County instrument data
    2. **Extract** addresses from PDFs using AI
    3. **Search** for property addresses using HCAD
    
    Complete steps in order for best results.
    """)
    
    # Initialize session state
    if "app1_results" not in st.session_state:
        st.session_state.app1_results = None
    if "app2_results" not in st.session_state:
        st.session_state.app2_results = None
    
    # Main content area
    if choice == "Step 1: Scrape Instruments":
        st.header("📊 Step 1: Scrape Instruments")
        st.markdown("Scrape instrument data from Harris County Clerk's Office records.")
        
        df = run_app1()
        if df is not None and not df.empty:
            st.session_state.app1_results = df
            st.success("✅ Data ready for PDF address extraction!")
    
    elif choice == "Step 2: Extract PDF Addresses":
        st.header("📄 Step 2: Extract PDF Addresses")
        st.markdown("Extract property addresses from PDF documents using AI-powered OCR.")
        
        if st.session_state.app1_results is not None:
            df = run_app2_pdf(st.session_state.app1_results)
            if df is not None and not df.empty:
                st.session_state.app2_results = df
                st.success("✅ Addresses extracted! Ready for HCAD search.")
        else:
            st.warning("⚠️ Please complete Step 1 first to get instrument data.")
    
    elif choice == "Step 3: HCAD Search":
        st.header("🔍 Step 3: HCAD Property Search")
        st.markdown("Search for property addresses using HCAD for records without PDF addresses.")
        
        # Use Step 2 results if available, otherwise use Step 1 results
        data_to_search = st.session_state.app2_results if st.session_state.app2_results is not None else st.session_state.app1_results
        
        if data_to_search is not None:
            run_app2_hcad(data_to_search)
        else:
            st.warning("⚠️ Please complete Step 1 first to get instrument data.")


if __name__ == "__main__":
    main()
