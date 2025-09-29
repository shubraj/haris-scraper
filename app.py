"""
Harris County Property Scraper - Main Application

A comprehensive tool for scraping Harris County instrument data and extracting
property addresses with AI-powered PDF processing and HCAD fallback.
"""
import streamlit as st
import os
import pandas as pd
import time
from apps.instrument_scraper import run_app1
from apps.unified_address_extractor import run_app2_unified
from utils.logger_config import get_app_logger

# Configure logging
logger = get_app_logger()

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
    
    # Custom CSS for smooth UI
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .success-container {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5a87 100%);
    }
    .stContainer {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f4e79;
    }
    .progress-section {
        margin: 1rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    .progress-item {
        margin: 0.5rem 0;
    }
    .stMarkdown h3 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .stMarkdown p {
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🏠 Harris County Property Scraper</h1>
        <p>Scrape instrument data and extract property addresses with AI-powered processing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📋 Workflow")
        st.markdown("""
        1. **Configure** your search parameters
        2. **Scrape** instrument data from Harris County
        3. **Auto-extract** addresses from PDFs using AI
        4. **Auto-fallback** to HCAD search for missing addresses
        5. **Download** your complete results
        """)
        
        st.markdown("---")
        st.markdown("### 🎯 Features")
        st.markdown("""
        - **Concurrent Processing**: Fast PDF and HCAD processing
        - **AI-Powered**: OpenAI GPT-4 for address extraction
        - **Smart Fallback**: HCAD search for missing addresses
        - **Progress Tracking**: Real-time progress bars
        - **Rate Limiting**: Optimized for API limits
        """)
    
    # Initialize session state
    if "scraped_data" not in st.session_state:
        st.session_state.scraped_data = None
    if "final_results" not in st.session_state:
        st.session_state.final_results = None
    if "workflow_step" not in st.session_state:
        st.session_state.workflow_step = "scrape"
    if "processing_state" not in st.session_state:
        st.session_state.processing_state = "idle"  # idle, processing, completed, error
    if "processing_started" not in st.session_state:
        st.session_state.processing_started = False
    if "can_resume" not in st.session_state:
        st.session_state.can_resume = False
    
    # Main workflow
    if st.session_state.workflow_step == "scrape":
        _show_scraping_step()
    elif st.session_state.workflow_step == "extract":
        _show_address_extraction_step()
    elif st.session_state.workflow_step == "complete":
        _show_final_results()

def _show_scraping_step():
    """Show the instrument scraping step."""
    with st.container():
        st.markdown("### 📊 Configure & Scrape Instruments")
        st.markdown("Configure your search parameters and scrape instrument data from Harris County records.")
        st.markdown("---")
    
    # Run the instrument scraper
        df = run_app1()
    
    if df is not None and not df.empty:
        st.session_state.scraped_data = df
        
        st.markdown('<div class="success-container">', unsafe_allow_html=True)
        st.success("✅ Scraping completed! Found {} records. Starting address extraction...".format(len(df)))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Auto-start address extraction
        st.session_state.workflow_step = "extract"
        st.rerun()

def _show_address_extraction_step():
    """Show the address extraction step."""
    # Header section
    with st.container():
        st.markdown("### 🔍 Extract Property Addresses")
        st.markdown("Extracting property addresses from PDFs using AI, with HCAD fallback for missing addresses.")
        st.markdown("---")
    
    if st.session_state.scraped_data is not None:
        # Check if we're in a processing state
        if st.session_state.processing_state == "processing":
            _show_processing_controls()
            return
        
        # Show processing info
        st.info(f"📊 Processing {len(st.session_state.scraped_data)} records for address extraction")
        
        # Control buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🚀 Start Address Extraction", type="primary", use_container_width=True):
                st.session_state.processing_state = "processing"
                st.session_state.processing_started = True
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset Process", use_container_width=True):
                _reset_processing_state()
                st.rerun()
        
        with col3:
            if st.button("🏠 Back to Scraping", use_container_width=True):
                st.session_state.workflow_step = "scrape"
                st.rerun()
        
        # Show existing results if any
        if st.session_state.get('live_results') and len(st.session_state.live_results) > 0:
            st.markdown("### 📊 Previous Results Found")
            st.info(f"Found {len(st.session_state.live_results)} results from previous processing. Click 'Start Address Extraction' to continue or 'Reset Process' to start fresh.")
            
            # Show existing results
            live_df = pd.DataFrame(st.session_state.live_results)
            st.dataframe(live_df, width='stretch')
    else:
        st.warning("⚠️ No scraped data available. Please restart the process.")

def _show_processing_controls():
    """Show processing controls and live results during processing."""
    st.markdown("### ⚙️ Processing Controls")
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏹️ Stop Processing", type="secondary", use_container_width=True):
            st.session_state.processing_state = "idle"
            st.session_state.processing_started = False
            st.warning("⚠️ Processing stopped. You can resume or start fresh.")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Process", use_container_width=True):
            _reset_processing_state()
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to Scraping", use_container_width=True):
            st.session_state.workflow_step = "scrape"
            st.rerun()
    
    st.markdown("---")
    
    # Show processing status
    if st.session_state.processing_state == "processing":
        st.info("🔄 Processing in progress... The page will update automatically as results are found.")
        
        # Show live results if available
        if st.session_state.get('live_results') and len(st.session_state.live_results) > 0:
            live_df = pd.DataFrame(st.session_state.live_results)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Records Processed", len(live_df))
            with col2:
                addresses_found = len(live_df[live_df['Property Address'] != ''])
                st.metric("Addresses Found", addresses_found)
            with col3:
                success_rate = (addresses_found / len(live_df)) * 100 if len(live_df) > 0 else 0
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Results table
            st.markdown("#### 📋 Live Results")
            st.dataframe(live_df, width='stretch')
        else:
            st.info("⏳ Processing started... Results will appear here as they are found.")
    
    # Auto-refresh every 2 seconds during processing
    if st.session_state.processing_state == "processing":
        time.sleep(2)
        st.rerun()

def _reset_processing_state():
    """Reset all processing-related session state."""
    st.session_state.processing_state = "idle"
    st.session_state.processing_started = False
    st.session_state.can_resume = False
    if 'live_results' in st.session_state:
        del st.session_state.live_results
    if 'live_results_df' in st.session_state:
        del st.session_state.live_results_df
    if 'hcad_results' in st.session_state:
        del st.session_state.hcad_results

def _show_final_results():
    """Show the final results with download options."""
    with st.container():
        st.markdown("### ✅ Complete Results")
        st.markdown("Your data has been processed with addresses extracted. Download your results below.")
        st.markdown("---")
    
    if st.session_state.final_results is not None:
        df = st.session_state.final_results
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            addresses_found = len(df[df['Property Address'] != ''])
            st.metric("Addresses Found", addresses_found)
        with col3:
            success_rate = (addresses_found / len(df)) * 100 if len(df) > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col4:
            if 'PdfUrl' in df.columns:
                pdf_records = len(df[df['PdfUrl'].notna() & (df['PdfUrl'] != '')])
            else:
                pdf_records = 0
            st.metric("PDF Records", pdf_records)
        
        # Results table
        st.subheader("📋 Results Preview")
        st.dataframe(df, width='stretch')
        
        # Download options
        st.subheader("📥 Download Results")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv,
                file_name="harris_county_property_data.csv",
                mime="text/csv",
                width='stretch'
            )
        
        with col2:
            # Excel download
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Property Data')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📈 Download Excel",
                data=excel_data,
                file_name="harris_county_property_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )
        
        # Reset button
        st.markdown("---")
        if st.button("🔄 Start New Search", width='stretch'):
            # Reset session state
            st.session_state.scraped_data = None
            st.session_state.final_results = None
            st.session_state.workflow_step = "scrape"
            st.rerun()


if __name__ == "__main__":
    main()
