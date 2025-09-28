#!/usr/bin/env python3
"""
CLI script to OCR PDF files.
Usage: python ocr_pdf.py <pdf_file> [output_file]
"""
import sys
import os
from utils.pdf_ocr import ocr_pdf_file


def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python ocr_pdf.py <pdf_file> [output_file]")
        print("Example: python ocr_pdf.py ViewEdocs.pdf ocr_results.txt")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(pdf_file):
        print(f"Error: PDF file not found: {pdf_file}")
        sys.exit(1)
    
    try:
        print(f"Starting OCR for: {pdf_file}")
        results = ocr_pdf_file(pdf_file, output_file, dpi=300)
        
        print(f"\n✅ OCR completed successfully!")
        print(f"📄 Processed {len(results)} pages")
        
        total_words = sum(result['word_count'] for result in results)
        total_chars = sum(result['character_count'] for result in results)
        
        print(f"📊 Total words: {total_words:,}")
        print(f"📊 Total characters: {total_chars:,}")
        
        if output_file:
            print(f"💾 Results saved to: {output_file}")
        else:
            print("\n📝 First 500 characters of each page:")
            for result in results[:3]:  # Show first 3 pages
                preview = result['text'][:500]
                print(f"\n--- Page {result['page_number']} ---")
                print(preview + "..." if len(result['text']) > 500 else preview)
    
    except Exception as e:
        print(f"❌ Error during OCR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
