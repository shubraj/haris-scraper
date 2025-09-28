"""
PDF Address Extraction Application - Step 2
Extract addresses from PDFs using OpenAI API.
"""
import streamlit as st
import pandas as pd
from typing import Optional, Dict, List
import tempfile
import os
from pathlib import Path

from scrapers.harris_county_scraper import get_scraper
from utils.address_extractor import AddressExtractor
from utils.pdf_ocr import PDFOCR
from utils.logger_config import get_app_logger

# Configure logging
logger = get_app_logger()


class PDFAddressExtractorApp:
    """Streamlit application for extracting addresses from PDFs."""
    
    def __init__(self):
        self.scraper = get_scraper()
        self.address_extractor = AddressExtractor()
        self.pdf_ocr = PDFOCR()
    
    def run(self, records_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Run the PDF address extraction application.
        
        Args:
            records_df: DataFrame with scraped records from Step 1
            
        Returns:
            DataFrame with extracted addresses or None if no data
        """
        st.header("📄 Step 2: Extract Addresses from PDFs")
        st.markdown("Extract property addresses from PDF documents using AI-powered OCR and address extraction.")
        
        if records_df is None or records_df.empty:
            st.warning("⚠️ No records available. Please complete Step 1 first.")
            return None
        
        # Filter records that have PdfUrl (PDF available)
        pdf_records = records_df[records_df['PdfUrl'].notna() & (records_df['PdfUrl'] != '')]
        
        if pdf_records.empty:
            st.warning("⚠️ No records with PDFs found. All records will proceed to HCAD search.")
            return records_df
        
        st.info(f"📊 Found {len(pdf_records)} records with PDFs out of {len(records_df)} total records")
        
        # Process PDFs automatically
        with st.spinner("Processing PDFs and extracting addresses..."):
            results = self._process_pdfs(pdf_records, dpi=300, ocr_mode="--psm 6")
            
            if results is not None:
                st.success(f"✅ Successfully processed {len(results)} records")
                
                # Display results
                st.write("### 📋 Extracted Addresses")
                self._display_results(results)
                
                # Download results
                self._download_results(results)
                
                return results
            else:
                st.error("❌ Failed to process PDFs")
                return records_df
    
    def _process_pdfs(self, pdf_records: pd.DataFrame, dpi: int, ocr_mode: str) -> Optional[pd.DataFrame]:
        """Process PDFs and extract addresses."""
        try:
            logger.info(f"Starting PDF address extraction for {len(pdf_records)} records")
            
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, (index, record) in enumerate(pdf_records.iterrows()):
                record_id = record.get('FileNo', f'record_{index}')
                status_text.text(f"Processing record {i+1}/{len(pdf_records)}: {record_id}")
                
                logger.info(f"Processing PDF for record {record_id}")
                
                # Download PDF
                pdf_path = self._download_pdf(record)
                if not pdf_path:
                    logger.warning(f"Failed to download PDF for record {record_id}")
                    results.append(self._create_result_record(record, None, "PDF download failed"))
                    progress_bar.progress((i + 1) / len(pdf_records))
                    continue
                
                # Extract text from PDF
                try:
                    ocr_results = self.pdf_ocr.ocr_pdf(pdf_path, dpi=dpi, config=ocr_mode)
                    pdf_text = " ".join([page['text'] for page in ocr_results])
                    
                    if not pdf_text.strip():
                        logger.warning(f"No text extracted from PDF for record {record_id}")
                        results.append(self._create_result_record(record, None, "No text extracted from PDF"))
                        progress_bar.progress((i + 1) / len(pdf_records))
                        continue
                    
                    # Extract addresses using OpenAI
                    addresses = self.address_extractor.extract_grantees_addresses_only(pdf_text)
                    
                    if addresses:
                        # Use the first address found
                        property_address = self.address_extractor.standardize_address(addresses[0])
                        logger.info(f"Found address for record {record_id}: {property_address}")
                        results.append(self._create_result_record(record, property_address, "Address extracted from PDF"))
                    else:
                        logger.warning(f"No addresses found in PDF for record {record_id}")
                        results.append(self._create_result_record(record, None, "No addresses found in PDF"))
                    
                except Exception as e:
                    logger.error(f"Error processing PDF for record {record_id}: {e}")
                    results.append(self._create_result_record(record, None, f"Error: {str(e)}"))
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                
                progress_bar.progress((i + 1) / len(pdf_records))
            
            status_text.text("✅ Processing completed!")
            
            # Create results DataFrame
            results_df = pd.DataFrame(results)
            logger.info(f"PDF address extraction completed - {len(results_df)} records processed")
            
            return results_df
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            st.error(f"Error processing PDFs: {e}")
            return None
    
    def _download_pdf(self, record: pd.Series) -> Optional[str]:
        """Download PDF for a record."""
        try:
            pdf_url = record.get('PdfUrl', '')
            if not pdf_url:
                logger.warning(f"No PdfUrl found in record: {record.get('FileNo', 'unknown')}")
                return None
            
            logger.info(f"Downloading PDF from URL: {pdf_url}")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download PDF
            success = self.scraper.download_pdf(pdf_url, temp_path)
            
            if success and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None
    
    def _create_result_record(self, original_record: pd.Series, property_address: Optional[str], status: str) -> Dict:
        """Create a result record with extracted address."""
        return {
            'Grantor': original_record.get('Grantors', ''),
            'Grantee': original_record.get('Grantees', ''),
            'Instrument Type': original_record.get('DocType', ''),
            'Recording Date': original_record.get('FileDate', ''),
            'Film Code (Ref)': original_record.get('FilmCode', ''),
            'Legal Description': original_record.get('LegalDescription', ''),
            'Property Address': property_address or ''
        }
    
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
            failed = len(results_df[results_df['Property Address'] == ''])
            st.metric("Not Found", failed)
        
        # Results table
        st.dataframe(results_df, width='stretch')
        
        # Address extraction summary
        st.write("### 📊 Address Extraction Summary")
        empty_addresses = len(results_df[results_df['Property Address'] == ''])
        found_addresses = len(results_df[results_df['Property Address'] != ''])
        
        summary_data = pd.DataFrame({
            'Status': ['Addresses Found', 'No Address Found'],
            'Count': [found_addresses, empty_addresses]
        })
        st.bar_chart(summary_data.set_index('Status'))
    
    def _download_results(self, results_df: pd.DataFrame):
        """Provide download option for results."""
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name="pdf_address_extraction_results.csv",
            mime="text/csv"
        )


def run_app2_pdf(records_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Convenience function to run the PDF address extraction app.
    
    Args:
        records_df: DataFrame with scraped records from Step 1
        
    Returns:
        DataFrame with extracted addresses or None
    """
    app = PDFAddressExtractorApp()
    return app.run(records_df)
