"""
PDF OCR Streamlit application.
"""
import streamlit as st
import os
import tempfile
from typing import List, Dict
from utils.pdf_ocr import PDFOCR, ocr_pdf_file


def run_pdf_ocr_app() -> None:
    """Run the PDF OCR Streamlit application."""
    st.title("📄 PDF OCR Tool")
    st.markdown("Extract text from PDF files using OCR technology.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a PDF file",
        type=['pdf'],
        help="Upload a PDF file to extract text using OCR"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        st.info(f"📊 File size: {uploaded_file.size:,} bytes")
        
        # OCR settings
        st.markdown("### ⚙️ OCR Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            dpi = st.slider("DPI (Image Quality)", 150, 600, 300, 
                           help="Higher DPI = better quality but slower processing")
        with col2:
            psm_mode = st.selectbox(
                "Text Recognition Mode",
                options=[
                    ("Automatic page segmentation", "--psm 3"),
                    ("Single text block", "--psm 6"),
                    ("Single text line", "--psm 7"),
                    ("Single word", "--psm 8"),
                    ("Single character", "--psm 10")
                ],
                format_func=lambda x: x[0],
                help="Choose how Tesseract should interpret the text"
            )[1]
        
        # Process button
        if st.button("🔍 Start OCR Processing", type="primary"):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Initialize progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Perform OCR
                with st.spinner("Processing PDF with OCR..."):
                    status_text.text("Converting PDF to images...")
                    progress_bar.progress(20)
                    
                    ocr = PDFOCR()
                    images = ocr.pdf_to_images(tmp_path, dpi)
                    
                    status_text.text(f"Performing OCR on {len(images)} pages...")
                    progress_bar.progress(40)
                    
                    results = []
                    for i, image in enumerate(images):
                        status_text.text(f"Processing page {i+1}/{len(images)}...")
                        text = ocr.ocr_image(image, psm_mode)
                        
                        results.append({
                            'page_number': i + 1,
                            'text': text,
                            'word_count': len(text.split()),
                            'character_count': len(text)
                        })
                        
                        progress_bar.progress(40 + (i + 1) * 50 // len(images))
                    
                    status_text.text("OCR completed!")
                    progress_bar.progress(100)
                
                # Display results
                st.markdown("### 📊 OCR Results")
                
                # Summary statistics
                total_words = sum(result['word_count'] for result in results)
                total_chars = sum(result['character_count'] for result in results)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pages Processed", len(results))
                with col2:
                    st.metric("Total Words", f"{total_words:,}")
                with col3:
                    st.metric("Total Characters", f"{total_chars:,}")
                
                # Page-by-page results
                st.markdown("### 📄 Extracted Text by Page")
                
                for result in results:
                    with st.expander(f"Page {result['page_number']} ({result['word_count']} words)"):
                        if result['text']:
                            st.text_area(
                                f"Text from page {result['page_number']}",
                                value=result['text'],
                                height=200,
                                key=f"page_{result['page_number']}"
                            )
                        else:
                            st.warning("No text found on this page")
                
                # Download options
                st.markdown("### 💾 Download Results")
                
                # Create downloadable text file
                full_text = ""
                for result in results:
                    full_text += f"=== PAGE {result['page_number']} ===\n"
                    full_text += f"Words: {result['word_count']}, Characters: {result['character_count']}\n"
                    full_text += "-" * 50 + "\n"
                    full_text += result['text'] + "\n\n"
                
                st.download_button(
                    label="📥 Download Full Text",
                    data=full_text,
                    file_name=f"{uploaded_file.name}_ocr_results.txt",
                    mime="text/plain"
                )
                
                # Search functionality
                st.markdown("### 🔍 Search in Text")
                search_term = st.text_input("Search for text in the extracted content:")
                
                if search_term:
                    matches = []
                    for result in results:
                        if search_term.lower() in result['text'].lower():
                            matches.append({
                                'page': result['page_number'],
                                'context': result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
                            })
                    
                    if matches:
                        st.success(f"Found {len(matches)} matches:")
                        for match in matches:
                            st.write(f"**Page {match['page']}:** {match['context']}")
                    else:
                        st.warning("No matches found")
                
                # Clean up temporary file
                os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"❌ Error during OCR processing: {e}")
                st.info("Make sure Tesseract OCR is installed on your system.")
                
                # Installation instructions
                with st.expander("📋 Installation Instructions"):
                    st.markdown("""
                    **For macOS:**
                    ```bash
                    brew install tesseract
                    ```
                    
                    **For Ubuntu/Debian:**
                    ```bash
                    sudo apt-get install tesseract-ocr
                    ```
                    
                    **For Windows:**
                    1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
                    2. Add to PATH or specify path in the code
                    """)


if __name__ == "__main__":
    run_pdf_ocr_app()
