"""
Harris County Property Scraper - Main Application

A comprehensive tool for scraping Harris County instrument data and performing
HCAD property searches.
"""
import streamlit as st
import os
import subprocess
import sys
from typing import Optional

from apps.instrument_scraper import run_app1
from apps.hcad_search import run_app2


def install_playwright() -> None:
    """Install Playwright browsers and system dependencies."""
    # Check if we're on Streamlit Cloud
    is_streamlit_cloud = os.environ.get("STREAMLIT_SHARING_MODE") == "true"
    
    if is_streamlit_cloud:
        # On Streamlit Cloud, install system dependencies first
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install-deps"], 
                          check=True, capture_output=True, timeout=60)
            st.success("✅ System dependencies installed!")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            st.info("System dependencies installation skipped, continuing...")
    
    try:
        # Install Playwright browsers
        subprocess.run([sys.executable, "-m", "playwright", "install"], 
                      check=True, capture_output=True, timeout=120)
        st.success("✅ Playwright browsers installed successfully!")
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to install Playwright: {e}")
        st.info("Please run 'playwright install' manually in your terminal.")
    except subprocess.TimeoutExpired:
        st.error("Playwright installation timed out. Please try again.")


def main() -> None:
    """Main application entry point."""
    # Set page config
    st.set_page_config(
        page_title="Harris County Property Scraper",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Install Playwright on first run
    if "playwright_installed" not in st.session_state:
        with st.spinner("Installing Playwright browsers..."):
            install_playwright()
            st.session_state.playwright_installed = True
    
    # Sidebar navigation
    st.sidebar.title("🏠 Harris County Property Scraper")
    st.sidebar.markdown("---")
    
    choice = st.sidebar.radio(
        "Select Step:",
        ["Step 1: Scrape Instruments", "Step 2: HCAD Search"],
        help="Step 1: Scrape instrument data from Harris County records\nStep 2: Search for property addresses using HCAD"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    This tool helps you:
    1. **Scrape** Harris County instrument data
    2. **Search** for property addresses using HCAD
    
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


if __name__ == "__main__":
    main()
