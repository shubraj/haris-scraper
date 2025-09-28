"""
Unified Address Extraction Application - Step 2
Extract addresses from PDFs using AI, fallback to HCAD search if needed.
"""
import streamlit as st
import pandas as pd
import asyncio
from typing import Optional, Dict, List
import tempfile
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.harris_county_scraper import get_scraper
from scrapers.hcad import run_hcad_searches
from utils.address_extractor import AddressExtractor
from utils.pdf_ocr import PDFOCR
from utils.logger_config import get_app_logger

# Configure logging
logger = get_app_logger()


class UnifiedAddressExtractorApp:
    """Unified application for extracting addresses from PDFs and HCAD fallback."""
    
    def __init__(self):
        self.scraper = get_scraper()
        self.address_extractor = AddressExtractor()
        self.pdf_ocr = PDFOCR()
    
    def run(self, records_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Run the unified address extraction application.
        
        Args:
            records_df: DataFrame with scraped records from Step 1
            
        Returns:
            DataFrame with extracted addresses or None if no data
        """
        if records_df is None or records_df.empty:
            st.warning("⚠️ No records available. Please complete Step 1 first.")
            return None
        
        st.info(f"📊 Processing {len(records_df)} records for address extraction")
        
        # Process with button
        if st.button("🔍 Extract Addresses (PDF + HCAD Fallback)", type="primary"):
            with st.spinner("Processing records and extracting addresses..."):
                results = self._process_all_records(records_df)
                
                if results is not None and not results.empty:
                    st.success(f"✅ Found addresses for {len(results)} records")
                    
                    # Display results
                    st.write("### 📋 Final Results")
                    self._display_results(results)
                    
                    # Download results
                    self._download_results(results)
                    
                    return results
                else:
                    st.warning("⚠️ No addresses found for any records. Please check the data or try different search parameters.")
                    return None
    
    def _process_all_records(self, records_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Process all records with PDF extraction and HCAD fallback."""
        try:
            logger.info(f"Starting unified address extraction for {len(records_df)} records")
            
            # Process records concurrently (5 at a time)
            final_results = self._process_records_concurrent(records_df)
            
            if final_results:
                final_df = pd.DataFrame(final_results)
                st.success(f"✅ Processing completed! Found addresses for {len(final_df)} out of {len(records_df)} records")
                logger.info(f"Unified address extraction completed - {len(final_df)} records with addresses found")
                return final_df
            else:
                st.warning("⚠️ No addresses found for any records")
                logger.warning("No addresses found from either PDF extraction or HCAD search")
                return None
                
        except Exception as e:
            logger.error(f"Unified address extraction failed: {e}")
            st.error(f"Error processing records: {e}")
            return None
    
    def _process_records_concurrent(self, records_df: pd.DataFrame) -> List[Dict]:
        """Process records concurrently with 5 at a time using ThreadPoolExecutor."""
        records_list = records_df.to_dict('records')
        final_results = []
        
        # Process in batches of 5
        batch_size = 5
        total_batches = (len(records_list) + batch_size - 1) // batch_size
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(0, len(records_list), batch_size):
            batch = records_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            status_text.text(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            # Process batch concurrently
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all tasks in the batch
                future_to_record = {
                    executor.submit(self._process_single_record, record): record 
                    for record in batch
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_record):
                    record = future_to_record[future]
                    try:
                        result = future.result()
                        if result:
                            final_results.append(result)
                            record_id = record.get('FileNo', 'unknown')
                            address = result.get('Property Address', '')
                            logger.info(f"✅ {record_id}: Found address: {address}")
                    except Exception as e:
                        record_id = record.get('FileNo', 'unknown')
                        logger.error(f"Error processing record {record_id}: {e}")
            
            # Update progress bar
            progress_bar.progress(batch_num / total_batches)
        
        # Clear status text
        status_text.text("✅ Processing completed!")
        
        return final_results
    
    def _process_single_record(self, record: Dict) -> Optional[Dict]:
        """Process a single record with PDF extraction and HCAD fallback."""
        record_id = record.get('FileNo', 'unknown')
        address_found = False
        result = None
        
        # Step 1: Try PDF extraction if PDF available
        if record.get('PdfUrl') and record.get('PdfUrl').strip():
            pdf_address = self._try_pdf_extraction(record)
            if pdf_address:
                result = self._create_result_record(record, pdf_address, 'PDF extraction')
                address_found = True
                logger.info(f"✅ {record_id}: Found address in PDF: {pdf_address}")
        
        # Step 2: If no address from PDF, try HCAD
        if not address_found:
            hcad_address = asyncio.run(self._try_hcad_extraction(record))
            if hcad_address:
                result = self._create_result_record(record, hcad_address, 'HCAD')
                address_found = True
                logger.info(f"✅ {record_id}: Found address via HCAD: {hcad_address}")
        
        if not address_found:
            logger.warning(f"❌ {record_id}: No address found")
        
        return result
    
    def _try_pdf_extraction(self, record: Dict) -> Optional[str]:
        """Try to extract address from PDF for a single record."""
        try:
            # Download PDF
            pdf_path = self._download_pdf(record)
            if not pdf_path:
                return None
            
            # Extract text and addresses
            ocr_results = self.pdf_ocr.ocr_pdf(pdf_path, dpi=300, config="--psm 6")
            pdf_text = " ".join([page['text'] for page in ocr_results])
            
            if pdf_text.strip():
                addresses = self.address_extractor.extract_grantees_addresses_only(pdf_text)
                if addresses:
                    return self.address_extractor.standardize_address(addresses[0])
            
            return None
            
        except Exception as e:
            logger.error(f"PDF extraction failed for record {record.get('FileNo', 'unknown')}: {e}")
            return None
        finally:
            if 'pdf_path' in locals() and os.path.exists(pdf_path):
                os.remove(pdf_path)
    
    async def _try_hcad_extraction(self, record: Dict) -> Optional[str]:
        """Try to extract address using HCAD for a single record."""
        try:
            # Create single record DataFrame
            hcad_df = pd.DataFrame([record])
            
            # Clear previous results
            if 'hcad_results' in st.session_state:
                del st.session_state.hcad_results
            
            # Run HCAD search
            results_placeholder = st.empty()
            await run_hcad_searches(hcad_df, results_placeholder)
            
            # Get result
            if 'hcad_results' in st.session_state and not st.session_state.hcad_results.empty:
                hcad_result = st.session_state.hcad_results.iloc[0]
                return hcad_result.get('Property Address', '') or None
            
            return None
            
        except Exception as e:
            logger.error(f"HCAD extraction failed for record {record.get('FileNo', 'unknown')}: {e}")
            return None
    
    def _process_pdf_records(self, pdf_records: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Process records with PDFs for address extraction."""
        if pdf_records.empty:
            return pd.DataFrame()
        
        try:
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, (index, record) in enumerate(pdf_records.iterrows()):
                record_id = record.get('FileNo', f'record_{index}')
                status_text.text(f"Processing PDF {i+1}/{len(pdf_records)}: {record_id}")
                
                # Download PDF
                pdf_path = self._download_pdf(record)
                if not pdf_path:
                    results.append(self._create_result_record(record, '', 'PDF download failed'))
                    progress_bar.progress((i + 1) / len(pdf_records))
                    continue
                
                # Extract text and addresses
                try:
                    ocr_results = self.pdf_ocr.ocr_pdf(pdf_path, dpi=300, config="--psm 6")
                    pdf_text = " ".join([page['text'] for page in ocr_results])
                    
                    # Store OCR text for debugging
                    self._save_ocr_text_for_debugging(record_id, pdf_text, ocr_results)
                    
                    if pdf_text.strip():
                        addresses = self.address_extractor.extract_grantees_addresses_only(pdf_text)
                        if addresses:
                            property_address = self.address_extractor.standardize_address(addresses[0])
                            results.append(self._create_result_record(record, property_address, 'PDF extraction'))
                        else:
                            results.append(self._create_result_record(record, '', 'No address in PDF'))
                    else:
                        results.append(self._create_result_record(record, '', 'No text in PDF'))
                    
                except Exception as e:
                    logger.error(f"Error processing PDF for record {record_id}: {e}")
                    results.append(self._create_result_record(record, '', f'PDF error: {str(e)}'))
                
                finally:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                
                progress_bar.progress((i + 1) / len(pdf_records))
            
            status_text.text("✅ PDF processing completed!")
            return pd.DataFrame(results) if results else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return None
    
    async def _process_hcad_records(self, hcad_records: List[Dict]) -> pd.DataFrame:
        """Process records using HCAD search."""
        if not hcad_records:
            return pd.DataFrame()
        
        try:
            hcad_df = pd.DataFrame(hcad_records)
            
            # Create placeholder for HCAD results
            results_placeholder = st.empty()
            
            # Clear any previous HCAD results
            if 'hcad_results' in st.session_state:
                del st.session_state.hcad_results
            
            # Run HCAD searches
            await run_hcad_searches(hcad_df, results_placeholder)
            
            # Get results from session state if available
            if 'hcad_results' in st.session_state:
                hcad_results = st.session_state.hcad_results
                logger.info(f"HCAD search completed - found {len(hcad_results)} results")
                return hcad_results
            else:
                logger.warning("No HCAD results found in session state")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"HCAD processing failed: {e}")
            return pd.DataFrame()
    
    def _download_pdf(self, record: Dict) -> Optional[str]:
        """Download PDF for a record."""
        try:
            pdf_url = record.get('PdfUrl', '')
            if not pdf_url:
                return None
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            success = self.scraper.download_pdf(pdf_url, temp_path)
            
            if success and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None
    
    def _create_result_record(self, original_record: Dict, property_address: str, source: str) -> Dict:
        """Create a result record with extracted address."""
        return {
            'FileNo': original_record.get('FileNo', ''),
            'Grantor': original_record.get('Grantors', ''),
            'Grantee': original_record.get('Grantees', ''),
            'Instrument Type': original_record.get('DocType', ''),
            'Recording Date': original_record.get('FileDate', ''),
            'Film Code (Ref)': original_record.get('FilmCode', ''),
            'Legal Description': original_record.get('LegalDescription', ''),
            'Property Address': property_address
        }
    
    def _display_results(self, results_df: pd.DataFrame):
        """Display extraction results."""
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Records", len(results_df))
        
        with col2:
            addresses_found = len(results_df[results_df['Property Address'] != ''])
            st.metric("Addresses Found", addresses_found)
        
        with col3:
            success_rate = (addresses_found / len(results_df)) * 100 if len(results_df) > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Results table
        st.dataframe(results_df, width='stretch')
    
    def _download_results(self, results_df: pd.DataFrame):
        """Provide download option for results."""
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name="unified_address_extraction_results.csv",
            mime="text/csv"
        )


def run_app2_unified(records_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Convenience function to run the unified address extraction app.
    
    Args:
        records_df: DataFrame with scraped records from Step 1
        
    Returns:
        DataFrame with extracted addresses or None
    """
    app = UnifiedAddressExtractorApp()
    return app.run(records_df)
