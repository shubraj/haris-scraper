"""
Harris County Property Scraper - Main Application

A comprehensive tool for scraping Harris County instrument data and performing
HCAD property searches.
"""
import streamlit as st
import os
from apps.instrument_scraper import run_app1
from apps.hcad_search import run_app2
from apps.pdf_ocr_app import run_pdf_ocr_app

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
        "Select Tool:",
        ["Step 1: Scrape Instruments", "Step 2: HCAD Search", "PDF OCR Tool"],
        help="Step 1: Scrape instrument data from Harris County records\nStep 2: Search for property addresses using HCAD\nPDF OCR: Extract text from PDF files"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    This tool helps you:
    1. **Scrape** Harris County instrument data
    2. **Search** for property addresses using HCAD
    3. **Extract text** from PDF files using OCR
    
    Make sure to complete Step 1 before running Step 2.
    """)
    
    # Initialize session state
    if "app1_results" not in st.session_state:
        st.session_state.app1_results = None
    
    # Main content area
    if choice == "Step 1: Scrape Instruments":
        st.header("📊 Step 1: Scrape Instruments")
        st.markdown("Scrape instrument data from Harris County Clerk's Office records.")
        
        df = run_app1()
        if df is not None and not df.empty:
            st.session_state.app1_results = df
            st.success("✅ Data ready for HCAD search!")
    
    elif choice == "Step 2: HCAD Search":
        st.header("🔍 Step 2: HCAD Property Search")
        st.markdown("Search for property addresses using the scraped instrument data.")
        
        if st.session_state.app1_results is not None:
            run_app2(st.session_state.app1_results)
        else:
            st.warning("⚠️ Please complete Step 1 first to get instrument data.")
    
    elif choice == "PDF OCR Tool":
        run_pdf_ocr_app()


if __name__ == "__main__":
    main()
