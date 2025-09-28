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
            
            # Step 1: Try PDF extraction for records with PDFs
            pdf_records = records_df[records_df['PdfUrl'].notna() & (records_df['PdfUrl'] != '')]
            hcad_records = records_df[records_df['PdfUrl'].isna() | (records_df['PdfUrl'] == '')]
            
            st.write(f"📄 **Step 1: PDF Extraction** - Processing {len(pdf_records)} records with PDFs")
            pdf_results = self._process_pdf_records(pdf_records)
            
            # Step 2: Identify records that need HCAD fallback
            records_needing_hcad = []
            
            # Add records that didn't have PDFs (always need HCAD)
            for _, record in hcad_records.iterrows():
                records_needing_hcad.append(record.to_dict())
            
            # Add records where PDF extraction didn't find addresses
            if pdf_results is not None and not pdf_results.empty:
                for _, pdf_record in pdf_results.iterrows():
                    if not pdf_record.get('Property Address', '').strip():
                        # Find original record for HCAD search
                        file_no = pdf_record.get('FileNo', '')
                        if file_no:
                            original_record = records_df[records_df['FileNo'] == file_no]
                            if not original_record.empty:
                                records_needing_hcad.append(original_record.iloc[0].to_dict())
            else:
                # If PDF processing failed completely, use all PDF records for HCAD
                for _, record in pdf_records.iterrows():
                    records_needing_hcad.append(record.to_dict())
            
            if records_needing_hcad:
                st.write(f"🔍 **Step 2: HCAD Search** - Processing {len(records_needing_hcad)} records")
                hcad_results = asyncio.run(self._process_hcad_records(records_needing_hcad))
            else:
                hcad_results = pd.DataFrame()
            
            # Combine results intelligently - only show records with addresses
            final_results = []
            
            # Add PDF results that have addresses
            if pdf_results is not None and not pdf_results.empty:
                for _, pdf_record in pdf_results.iterrows():
                    if pdf_record.get('Property Address', '').strip():
                        final_results.append(pdf_record.to_dict())
            
            # Add HCAD results that have addresses
            if not hcad_results.empty:
                logger.info(f"Processing {len(hcad_results)} HCAD results")
                for _, hcad_record in hcad_results.iterrows():
                    address = hcad_record.get('Property Address', '')
                    if address and address.strip():
                        logger.info(f"Adding HCAD result with address: {address}")
                        final_results.append(hcad_record.to_dict())
                    else:
                        logger.debug(f"Skipping HCAD result with empty address: {hcad_record.get('FileNo', 'unknown')}")
            else:
                logger.warning("No HCAD results to process")
            
            if final_results:
                final_df = pd.DataFrame(final_results)
                logger.info(f"Unified address extraction completed - {len(final_df)} records with addresses found")
                return final_df
            else:
                logger.warning("No addresses found from either PDF extraction or HCAD search")
                return None
                
        except Exception as e:
            logger.error(f"Unified address extraction failed: {e}")
            st.error(f"Error processing records: {e}")
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
    
    def _download_pdf(self, record: pd.Series) -> Optional[str]:
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
    
    def _create_result_record(self, original_record: pd.Series, property_address: str, source: str) -> Dict:
        """Create a result record with extracted address."""
        return {
            'FileNo': original_record.get('FileNo', ''),
            'Grantor': original_record.get('Grantors', ''),
            'Grantee': original_record.get('Grantees', ''),
            'Instrument Type': original_record.get('DocType', ''),
            'Recording Date': original_record.get('FileDate', ''),
            'Film Code (Ref)': original_record.get('FilmCode', ''),
            'Legal Description': original_record.get('LegalDescription', ''),
            'Property Address': property_address,
            'Source': source
        }
    
    def _save_ocr_text_for_debugging(self, record_id: str, pdf_text: str, ocr_results: List[Dict]) -> None:
        """Save OCR text to file for debugging purposes."""
        try:
            debug_dir = "debug_ocr"
            os.makedirs(debug_dir, exist_ok=True)
            
            text_file = os.path.join(debug_dir, f"ocr_text_{record_id}.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"Record ID: {record_id}\n")
                f.write(f"OCR Text Length: {len(pdf_text)} characters\n")
                f.write(f"Number of Pages: {len(ocr_results)}\n")
                f.write("=" * 50 + "\n\n")
                f.write("FULL OCR TEXT:\n")
                f.write(pdf_text)
                f.write("\n\n" + "=" * 50 + "\n\n")
                f.write("PAGE-BY-PAGE BREAKDOWN:\n\n")
                
                for i, page_result in enumerate(ocr_results):
                    f.write(f"--- PAGE {i + 1} ---\n")
                    f.write(f"Word Count: {page_result.get('word_count', 0)}\n")
                    f.write(f"Character Count: {page_result.get('character_count', 0)}\n")
                    f.write("Text:\n")
                    f.write(page_result.get('text', ''))
                    f.write("\n\n")
            
            logger.info(f"OCR text saved for debugging: {text_file}")
            
        except Exception as e:
            logger.error(f"Failed to save OCR text for debugging: {e}")
    
    def _display_results(self, results_df: pd.DataFrame):
        """Display extraction results."""
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", len(results_df))
        
        with col2:
            addresses_found = len(results_df[results_df['Property Address'] != ''])
            st.metric("Addresses Found", addresses_found)
        
        with col3:
            success_rate = (addresses_found / len(results_df)) * 100 if len(results_df) > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col4:
            pdf_count = len(results_df[results_df['Source'] == 'PDF extraction'])
            st.metric("From PDFs", pdf_count)
        
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
