"""
PDF OCR utility for extracting text from PDF files using OCR.
"""
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import List, Dict, Optional, Tuple
from utils.logger_config import get_utils_logger

# Configure logging
logger = get_utils_logger()


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
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR engine initialized successfully - version: {version}")
        except Exception as e:
            logger.error(f"Tesseract OCR engine not found or not accessible: {e}")
            # Try to find tesseract in common locations
            common_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
                '/usr/bin/tesseract-ocr',
                '/usr/local/bin/tesseract-ocr'
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"Found tesseract at {path}, setting as command")
                    pytesseract.pytesseract.tesseract_cmd = path
                    try:
                        version = pytesseract.get_tesseract_version()
                        logger.info(f"Tesseract OCR engine initialized successfully - version: {version}")
                        break
                    except Exception:
                        continue
            else:
                logger.error("Could not find tesseract in any common locations")
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
            logger.info(f"Starting PDF to image conversion: {pdf_path} at {dpi} DPI")
            # Open PDF in read-only mode to prevent any modifications
            doc = fitz.open(pdf_path)
            images = []
            
            logger.info(f"PDF contains {len(doc)} pages - converting to images")
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Convert page to image without modifying the original
                mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
                logger.debug(f"Successfully converted page {page_num + 1}/{len(doc)} to image ({img.size[0]}x{img.size[1]} pixels)")
            
            doc.close()
            logger.info(f"PDF to image conversion completed - generated {len(images)} images")
            return images
            
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {type(e).__name__}: {e}")
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
            
            # Check if image is valid
            if image.size[0] == 0 or image.size[1] == 0:
                logger.warning("Skipping OCR for empty image")
                return ""
            
            # Try different OCR configurations if the default fails
            configs_to_try = [
                config,  # Original config
                "--psm 3",  # Fully automatic page segmentation
                "--psm 1",  # Automatic page segmentation with OSD
                "--psm 6",  # Uniform block of text
                ""  # No config
            ]
            
            for ocr_config in configs_to_try:
                try:
                    if ocr_config:
                        text = pytesseract.image_to_string(image, config=ocr_config)
                    else:
                        text = pytesseract.image_to_string(image)
                    
                    if text.strip():  # If we got some text, return it
                        logger.debug(f"OCR successful with config: {ocr_config or 'default'}")
                        return text.strip()
                        
                except Exception as ocr_error:
                    logger.debug(f"OCR failed with config '{ocr_config}': {ocr_error}")
                    continue
            
            # If all configs failed, try with image preprocessing
            logger.warning("All OCR configs failed, trying with image preprocessing")
            return self._ocr_with_preprocessing(image)
            
        except Exception as e:
            logger.error(f"Error performing OCR on image: {e}")
            return ""
    
    def _ocr_with_preprocessing(self, image: Image.Image) -> str:
        """
        Perform OCR with image preprocessing to improve results.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            
            # Try different preprocessing techniques
            preprocessed_images = [
                image,  # Original
                image.convert('L'),  # Grayscale
                ImageEnhance.Contrast(image).enhance(2.0),  # High contrast
                image.filter(ImageFilter.SHARPEN),  # Sharpened
                ImageEnhance.Contrast(image.convert('L')).enhance(2.0),  # Grayscale + contrast
            ]
            
            for i, processed_image in enumerate(preprocessed_images):
                try:
                    # Ensure RGB mode
                    if processed_image.mode != 'RGB':
                        processed_image = processed_image.convert('RGB')
                    
                    # Try OCR with different configs
                    for config in ["--psm 6", "--psm 3", "--psm 1", ""]:
                        try:
                            if config:
                                text = pytesseract.image_to_string(processed_image, config=config)
                            else:
                                text = pytesseract.image_to_string(processed_image)
                            
                            if text.strip():
                                logger.debug(f"OCR successful with preprocessing {i} and config: {config or 'default'}")
                                return text.strip()
                                
                        except Exception:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Preprocessing {i} failed: {e}")
                    continue
            
            logger.warning("All OCR attempts failed, including preprocessing")
            return ""
            
        except Exception as e:
            logger.error(f"Error in OCR preprocessing: {e}")
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
            logger.info(f"Starting OCR processing for PDF: {pdf_path} (DPI: {dpi}, Config: {config})")
            
            # Verify PDF file exists and is readable
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            file_size = os.path.getsize(pdf_path)
            logger.info(f"PDF file verified - size: {file_size:,} bytes")
            
            # Convert PDF to images (this doesn't modify the original PDF)
            images = self.pdf_to_images(pdf_path, dpi)
            
            results = []
            total_words = 0
            total_chars = 0
            
            for page_num, image in enumerate(images):
                logger.info(f"Performing OCR on page {page_num + 1}/{len(images)}")
                
                # Perform OCR on this page
                text = self.ocr_image(image, config)
                
                word_count = len(text.split())
                char_count = len(text)
                total_words += word_count
                total_chars += char_count
                
                results.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'word_count': word_count,
                    'character_count': char_count
                })
                
                logger.debug(f"Page {page_num + 1} OCR completed - {word_count} words, {char_count} characters")
            
            logger.info(f"OCR processing completed successfully - {len(images)} pages processed, {total_words:,} total words, {total_chars:,} total characters")
            return results
            
        except Exception as e:
            logger.error(f"OCR processing failed for PDF {pdf_path}: {type(e).__name__}: {e}")
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
            
            # Get the region without modifying the original page
            rect = fitz.Rect(bbox)
            
            # Convert to image with crop applied during rendering (not modifying page)
            mat = fitz.Matrix(dpi/72, dpi/72)
            # Use get_pixmap with clip parameter instead of set_cropbox
            pix = page.get_pixmap(matrix=mat, clip=rect)
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
