"""
PDF OCR utility for extracting text from PDF files using OCR.
"""
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFOCR:
    """PDF OCR utility for extracting text from PDF files."""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize PDF OCR utility.
        
        Args:
            tesseract_path: Path to tesseract executable (if not in PATH)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Verify tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is available")
        except Exception as e:
            logger.error(f"Tesseract OCR not found: {e}")
            raise
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[Image.Image]:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion (higher = better quality, slower)
            
        Returns:
            List of PIL Images
        """
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Convert page to image
                mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
                logger.info(f"Converted page {page_num + 1} to image")
            
            doc.close()
            return images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise
    
    def ocr_image(self, image: Image.Image, config: str = "--psm 6") -> str:
        """
        Perform OCR on a single image.
        
        Args:
            image: PIL Image object
            config: Tesseract configuration string
            
        Returns:
            Extracted text
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=config)
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error performing OCR on image: {e}")
            return ""
    
    def ocr_pdf(self, pdf_path: str, dpi: int = 300, config: str = "--psm 6") -> List[Dict[str, any]]:
        """
        Perform OCR on entire PDF file.
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion
            config: Tesseract configuration
            
        Returns:
            List of dictionaries with page info and extracted text
        """
        try:
            logger.info(f"Starting OCR for PDF: {pdf_path}")
            
            # Convert PDF to images
            images = self.pdf_to_images(pdf_path, dpi)
            
            results = []
            for page_num, image in enumerate(images):
                logger.info(f"Processing page {page_num + 1}/{len(images)}")
                
                # Perform OCR on this page
                text = self.ocr_image(image, config)
                
                results.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'word_count': len(text.split()),
                    'character_count': len(text)
                })
            
            logger.info(f"OCR completed for {len(images)} pages")
            return results
            
        except Exception as e:
            logger.error(f"Error performing OCR on PDF: {e}")
            raise
    
    def extract_text_by_region(self, pdf_path: str, page_num: int, 
                             bbox: Tuple[int, int, int, int], 
                             dpi: int = 300) -> str:
        """
        Extract text from a specific region of a PDF page.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            bbox: Bounding box (x0, y0, x1, y1)
            dpi: DPI for image conversion
            
        Returns:
            Extracted text from the region
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_num)
            
            # Get the region
            rect = fitz.Rect(bbox)
            page.set_cropbox(rect)
            
            # Convert to image
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            text = self.ocr_image(img)
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from region: {e}")
            return ""
    
    def save_ocr_results(self, results: List[Dict[str, any]], output_path: str) -> None:
        """
        Save OCR results to a text file.
        
        Args:
            results: OCR results from ocr_pdf
            output_path: Path to save the text file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(f"=== PAGE {result['page_number']} ===\n")
                    f.write(f"Words: {result['word_count']}, Characters: {result['character_count']}\n")
                    f.write("-" * 50 + "\n")
                    f.write(result['text'])
                    f.write("\n\n")
            
            logger.info(f"OCR results saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving OCR results: {e}")
            raise


def ocr_pdf_file(pdf_path: str, output_path: Optional[str] = None, 
                dpi: int = 300, tesseract_path: Optional[str] = None) -> List[Dict[str, any]]:
    """
    Convenience function to OCR a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Optional path to save results
        dpi: DPI for image conversion
        tesseract_path: Path to tesseract executable
        
    Returns:
        OCR results
    """
    ocr = PDFOCR(tesseract_path)
    results = ocr.ocr_pdf(pdf_path, dpi)
    
    if output_path:
        ocr.save_ocr_results(results, output_path)
    
    return results


if __name__ == "__main__":
    # Example usage
    pdf_file = "ViewEdocs.pdf"
    
    if os.path.exists(pdf_file):
        print(f"Starting OCR for {pdf_file}...")
        results = ocr_pdf_file(pdf_file, "ocr_results.txt")
        
        print(f"OCR completed! Processed {len(results)} pages.")
        for result in results:
            print(f"Page {result['page_number']}: {result['word_count']} words")
    else:
        print(f"PDF file not found: {pdf_file}")
