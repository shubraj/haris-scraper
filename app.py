"""
Harris County Property Scraper - Main Application

A comprehensive tool for scraping Harris County instrument data and performing
HCAD property searches.
"""
import streamlit as st
import os
from apps.instrument_scraper import run_app1
from apps.unified_address_extractor import run_app2_unified

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
    
    # Initialize session state
    if "app1_results" not in st.session_state:
        st.session_state.app1_results = None
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1
    if "step1_completed" not in st.session_state:
        st.session_state.step1_completed = False
    if "step2_completed" not in st.session_state:
        st.session_state.step2_completed = False
    
    # Sidebar navigation
    st.sidebar.title("🏠 Harris County Property Scraper")
    st.sidebar.markdown("---")
    
    # Progress indicator
    st.sidebar.markdown("### Progress")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.session_state.step1_completed:
            st.success("✅ Step 1")
        else:
            st.info("⏳ Step 1")
    with col2:
        if st.session_state.step2_completed:
            st.success("✅ Step 2")
        else:
            st.info("⏳ Step 2")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    This tool helps you:
    1. **Scrape** Harris County instrument data
    2. **Extract** addresses from PDFs and HCAD fallback
    
    Steps will progress automatically.
    """)
    
    # Main content area with smooth transitions
    if st.session_state.current_step == 1:
        _render_step1()
    elif st.session_state.current_step == 2:
        _render_step2()
    else:
        _render_completion()


def _render_step1():
    """Render Step 1: Scrape Instruments."""
    st.header("📊 Step 1: Scrape Instruments")
    st.markdown("Scrape instrument data from Harris County Clerk's Office records.")
    
    # Add some visual flair
    st.markdown("---")
    
    df = run_app1()
    if df is not None and not df.empty:
        st.session_state.app1_results = df
        st.session_state.step1_completed = True
        
        # Success message with auto-progression
        st.success("✅ Data ready for address extraction!")
        st.balloons()
        
        # Auto-progress to Step 2
        st.markdown("### 🚀 Automatically proceeding to Step 2...")
        st.session_state.current_step = 2
        st.rerun()


def _render_step2():
    """Render Step 2: Extract Addresses."""
    st.header("🔍 Step 2: Extract Addresses")
    st.markdown("Extract property addresses from PDFs using AI, with HCAD fallback for missing addresses.")
    
    # Add some visual flair
    st.markdown("---")
    
    if st.session_state.app1_results is not None:
        df = run_app2_unified(st.session_state.app1_results)
        if df is not None and not df.empty:
            st.session_state.app1_results = df  # Update with addresses
            st.session_state.step2_completed = True
            
            # Success message
            st.success("✅ Address extraction completed!")
            st.balloons()
            
            # Show completion options
            st.markdown("### 🎉 All Steps Completed!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Start Over", type="secondary"):
                    _reset_session()
            with col2:
                if st.button("📊 View Results", type="primary"):
                    st.session_state.current_step = 3
                    st.rerun()
        else:
            st.warning("⚠️ No addresses found. Please check the data or try different search parameters.")
    else:
        st.warning("⚠️ Please complete Step 1 first to get instrument data.")
        if st.button("⬅️ Go to Step 1", type="secondary"):
            st.session_state.current_step = 1
            st.rerun()


def _render_completion():
    """Render completion view with results."""
    st.header("🎉 Process Complete!")
    st.markdown("All steps have been completed successfully.")
    
    if st.session_state.app1_results is not None:
        st.markdown("### 📊 Final Results")
        st.dataframe(st.session_state.app1_results, use_container_width=True)
        
        # Download button
        csv = st.session_state.app1_results.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name="harris_county_property_data.csv",
            mime="text/csv",
            type="primary"
        )
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start New Process", type="primary"):
            _reset_session()
    with col2:
        if st.button("⬅️ Back to Step 2", type="secondary"):
            st.session_state.current_step = 2
            st.rerun()


def _reset_session():
    """Reset the session state to start over."""
    st.session_state.app1_results = None
    st.session_state.current_step = 1
    st.session_state.step1_completed = False
    st.session_state.step2_completed = False
    st.rerun()


if __name__ == "__main__":
    main()
