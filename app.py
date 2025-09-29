"""
Harris County Property Scraper - Main Application

A comprehensive tool for scraping Harris County instrument data and extracting
property addresses with AI-powered PDF processing and HCAD fallback.
"""
import streamlit as st
import os
import pandas as pd
import json
import pickle
from datetime import datetime
from apps.instrument_scraper import run_app1
from apps.unified_address_extractor import run_app2_unified
from utils.logger_config import get_app_logger

# Configure logging
logger = get_app_logger()

# Install Playwright
os.system("playwright install")

# State persistence functions
def save_state():
    """Save current session state to file."""
    try:
        state_data = {
            'scraped_data': st.session_state.scraped_data,
            'final_results': st.session_state.final_results,
            'workflow_step': st.session_state.workflow_step,
            'processing_started': st.session_state.processing_started,
            'processing_completed': st.session_state.processing_completed,
            'processing_error': st.session_state.processing_error,
            'stop_processing': st.session_state.stop_processing,
            'live_results': st.session_state.get('live_results', []),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to file
        with open('session_state.pkl', 'wb') as f:
            pickle.dump(state_data, f)
        
        logger.info("Session state saved successfully")
    except Exception as e:
        logger.error(f"Failed to save session state: {e}")

def load_state():
    """Load session state from file."""
    try:
        if os.path.exists('session_state.pkl'):
            with open('session_state.pkl', 'rb') as f:
                state_data = pickle.load(f)
            
            # Check if state is recent (within last 24 hours)
            if 'timestamp' in state_data:
                state_time = datetime.fromisoformat(state_data['timestamp'])
                if (datetime.now() - state_time).total_seconds() < 24 * 3600:  # 24 hours
                    # Load state
                    st.session_state.scraped_data = state_data.get('scraped_data')
                    st.session_state.final_results = state_data.get('final_results')
                    st.session_state.workflow_step = state_data.get('workflow_step', 'scrape')
                    st.session_state.processing_started = state_data.get('processing_started', False)
                    st.session_state.processing_completed = state_data.get('processing_completed', False)
                    st.session_state.processing_error = state_data.get('processing_error')
                    st.session_state.stop_processing = state_data.get('stop_processing', False)
                    st.session_state.live_results = state_data.get('live_results', [])
                    
                    logger.info("Session state loaded successfully")
                    return True
                else:
                    logger.info("Session state is too old, starting fresh")
                    return False
            else:
                logger.info("No timestamp in saved state, starting fresh")
                return False
        else:
            logger.info("No saved session state found")
            return False
    except Exception as e:
        logger.error(f"Failed to load session state: {e}")
        return False

def clear_state():
    """Clear saved state file."""
    try:
        if os.path.exists('session_state.pkl'):
            os.remove('session_state.pkl')
        logger.info("Session state cleared")
    except Exception as e:
        logger.error(f"Failed to clear session state: {e}")

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
    
    # Try to load existing state first
    state_loaded = load_state()
    
    # Initialize session state (only if not loaded from file)
    if not state_loaded:
        if "scraped_data" not in st.session_state:
            st.session_state.scraped_data = None
        if "final_results" not in st.session_state:
            st.session_state.final_results = None
        if "workflow_step" not in st.session_state:
            st.session_state.workflow_step = "scrape"
        if "processing_started" not in st.session_state:
            st.session_state.processing_started = False
        if "processing_completed" not in st.session_state:
            st.session_state.processing_completed = False
        if "processing_error" not in st.session_state:
            st.session_state.processing_error = None
        if "stop_processing" not in st.session_state:
            st.session_state.stop_processing = False
        if "live_results" not in st.session_state:
            st.session_state.live_results = []
    
    # Show state recovery message if loaded
    if state_loaded:
        if st.session_state.processing_started and not st.session_state.processing_completed and not st.session_state.stop_processing:
            st.info("🔄 **State Recovered**: Processing was in progress. You can continue or stop the process.")
        elif st.session_state.processing_completed:
            st.success("✅ **State Recovered**: Processing was completed. Showing results...")
        elif st.session_state.stop_processing:
            st.warning("⏹️ **State Recovered**: Processing was stopped. You can retry or start fresh.")
    
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
        save_state()  # Save state before moving to extraction
        st.rerun()

def _show_address_extraction_step():
    """Show the address extraction step."""
    # Header section
    with st.container():
        st.markdown("### 🔍 Extract Property Addresses")
        st.markdown("Extracting property addresses from PDFs using AI, with HCAD fallback for missing addresses.")
        st.markdown("---")
    
    if st.session_state.scraped_data is not None:
        # Check if processing was already completed
        if st.session_state.processing_completed:
            st.success("✅ Address extraction completed! Moving to results...")
            st.session_state.workflow_step = "complete"
            save_state()  # Save state before moving to results
            st.rerun()
            return
        
        # Check if there was an error
        if st.session_state.processing_error:
            st.error(f"❌ Processing failed with error: {st.session_state.processing_error}")
            if st.button("🔄 Retry Processing"):
                st.session_state.processing_error = None
                st.session_state.processing_started = False
                save_state()  # Save state after retry
                st.rerun()
            return
        
        # Show stop button if processing is active
        if st.session_state.processing_started and not st.session_state.stop_processing:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📊 Processing {len(st.session_state.scraped_data)} records for address extraction")
            with col2:
                if st.button("⏹️ Stop Processing", type="secondary"):
                    st.session_state.stop_processing = True
                    save_state()  # Save state when stopping
                    st.rerun()
        
        # Simple progress display
        if not st.session_state.processing_started:
            st.info(f"📊 Ready to process {len(st.session_state.scraped_data)} records for address extraction")
        
        # Single progress bar with status
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create placeholders for live results
        live_results_placeholder = st.empty()
        
        # Start or continue processing
        if not st.session_state.processing_started and not st.session_state.stop_processing:
            # Start processing
            st.session_state.processing_started = True
            st.session_state.stop_processing = False
            st.session_state.processing_error = None
            save_state()  # Save state when starting processing
            
            # Auto-start address extraction with progress tracking
            try:
                # Update status
                status_text.text("🚀 Starting address extraction process...")
                progress_bar.progress(0.1)
                
                # Create progress callback function
                def update_progress(progress_value, message):
                    if st.session_state.stop_processing:
                        return False  # Signal to stop
                    progress_bar.progress(progress_value)
                    status_text.text(message)
                    return True  # Continue processing
                
                # Run address extraction with progress callback
                df = run_app2_unified(st.session_state.scraped_data, update_progress)
                
                if st.session_state.stop_processing:
                    status_text.text("⏹️ Processing stopped by user")
                    st.warning("Processing was stopped. You can restart it anytime.")
                    return
                
                if df is not None and not df.empty:
                    # Update progress to complete
                    progress_bar.progress(1.0)
                    status_text.text("✅ Address extraction completed!")
                    
                    # Clear live results placeholder
                    live_results_placeholder.empty()
                    
                    st.session_state.final_results = df
                    st.session_state.processing_completed = True
                    st.session_state.workflow_step = "complete"
                    save_state()  # Save state when processing completes
                    st.rerun()
                else:
                    progress_bar.progress(0)
                    status_text.text("❌ Address extraction failed")
                    st.error("❌ Address extraction failed. No addresses found for any records.")
                    st.session_state.processing_error = "No addresses found for any records"
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("❌ Address extraction failed")
                st.error(f"❌ Address extraction failed with error: {str(e)}")
                logger.error(f"Address extraction error: {e}")
                st.session_state.processing_error = str(e)
        elif st.session_state.stop_processing:
            status_text.text("⏹️ Processing stopped by user")
            st.warning("Processing was stopped. Click 'Retry Processing' to restart.")
            if st.button("🔄 Retry Processing"):
                st.session_state.stop_processing = False
                st.session_state.processing_started = False
                st.session_state.processing_error = None
                save_state()  # Save state when retrying
                st.rerun()
    else:
        st.warning("⚠️ No scraped data available. Please restart the process.")

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
            # Reset all session state
            st.session_state.scraped_data = None
            st.session_state.final_results = None
            st.session_state.workflow_step = "scrape"
            st.session_state.processing_started = False
            st.session_state.processing_completed = False
            st.session_state.processing_error = None
            st.session_state.stop_processing = False
            if 'live_results' in st.session_state:
                del st.session_state.live_results
            if 'live_results_df' in st.session_state:
                del st.session_state.live_results_df
            clear_state()  # Clear saved state file
            st.rerun()


if __name__ == "__main__":
    main()
