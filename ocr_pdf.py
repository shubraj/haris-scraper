#!/usr/bin/env python3
"""
Command-line interface for PDF OCR utility.
Optimized for processing thousands of PDFs efficiently with watermark removal.
"""
import argparse
import sys
from pathlib import Path
from utils.pdf_ocr import ocr_pdf_file, batch_ocr_directory


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files using OCR with watermark removal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single PDF
  python ocr_pdf.py document.pdf
  python ocr_pdf.py document.pdf -o output.txt
  
  # Batch processing
  python ocr_pdf.py --batch input_dir output_dir
  
  # High quality with watermark removal
  python ocr_pdf.py document.pdf -d 300 --remove-watermarks
  
  # Fast processing
  python ocr_pdf.py document.pdf -d 150 --no-parallel
        """
    )
    
    # Input arguments
    parser.add_argument(
        "input",
        help="PDF file path or directory (for batch processing)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: <pdf_name>_ocr.txt)"
    )
    
    # Processing options
    parser.add_argument(
        "-d", "--dpi",
        type=int,
        default=300,
        help="DPI for image conversion (default: 300)"
    )
    
    parser.add_argument(
        "--remove-watermarks",
        action="store_true",
        default=True,
        help="Remove watermarks and enhance images (default: True)"
    )
    
    parser.add_argument(
        "--no-remove-watermarks",
        action="store_true",
        help="Disable watermark removal"
    )
    
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel processing"
    )
    
    # Batch processing
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all PDFs in input directory"
    )
    
    parser.add_argument(
        "-t", "--tesseract-path",
        help="Path to tesseract executable"
    )
    
    args = parser.parse_args()
    
    # Handle watermark removal setting
    remove_watermarks = args.remove_watermarks and not args.no_remove_watermarks
    parallel = not args.no_parallel
    
    if args.batch:
        # Batch processing mode
        input_dir = Path(args.input)
        if not input_dir.exists() or not input_dir.is_dir():
            print(f"Error: Input directory '{input_dir}' not found")
            sys.exit(1)
        
        if not args.output:
            print("Error: Output directory required for batch processing")
            sys.exit(1)
        
        output_dir = Path(args.output)
        
        try:
            print(f"🔄 Starting batch OCR processing...")
            print(f"📁 Input directory: {input_dir}")
            print(f"📁 Output directory: {output_dir}")
            print(f"🔧 DPI: {args.dpi}")
            print(f"🚫 Watermark removal: {'Yes' if remove_watermarks else 'No'}")
            print(f"⚡ Parallel processing: {'Yes' if parallel else 'No'}")
            print()
            
            # Perform batch OCR
            summary = batch_ocr_directory(
                str(input_dir),
                str(output_dir),
                dpi=args.dpi,
                remove_watermarks=remove_watermarks,
                tesseract_path=args.tesseract_path
            )
            
            # Print summary
            print(f"\n✅ Batch processing completed!")
            print(f"📊 Processed: {summary['processed']}/{summary['total']} PDFs")
            print(f"⏱️  Total time: {summary['total_time']:.2f} seconds")
            print(f"⚡ Average time per PDF: {summary['avg_time_per_pdf']:.2f} seconds")
            
            if summary['failed'] > 0:
                print(f"❌ Failed: {summary['failed']} PDFs")
        
        except Exception as e:
            print(f"❌ Error during batch processing: {e}")
            sys.exit(1)
    
    else:
        # Single file processing mode
        pdf_path = Path(args.input)
        if not pdf_path.exists():
            print(f"Error: PDF file '{pdf_path}' not found")
            sys.exit(1)
        
        if not pdf_path.suffix.lower() == '.pdf':
            print(f"Error: File '{pdf_path}' is not a PDF")
            sys.exit(1)
        
        # Generate output path if not provided
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = pdf_path.parent / f"{pdf_path.stem}_ocr.txt"
        
        try:
            print(f"🔄 Processing PDF: {pdf_path}")
            print(f"💾 Output: {output_path}")
            print(f"🔧 DPI: {args.dpi}")
            print(f"🚫 Watermark removal: {'Yes' if remove_watermarks else 'No'}")
            print(f"⚡ Parallel processing: {'Yes' if parallel else 'No'}")
            print()
            
            # Perform OCR
            results = ocr_pdf_file(
                str(pdf_path),
                str(output_path),
                dpi=args.dpi,
                tesseract_path=args.tesseract_path,
                remove_watermarks=remove_watermarks,
                parallel=parallel
            )
            
            # Print summary
            total_pages = len(results)
            total_words = sum(page['word_count'] for page in results)
            total_chars = sum(page['character_count'] for page in results)
            
            print(f"\n✅ OCR completed successfully!")
            print(f"📄 Pages processed: {total_pages}")
            print(f"📝 Total words: {total_words}")
            print(f"🔤 Total characters: {total_chars}")
            print(f"💾 Results saved to: {output_path}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()