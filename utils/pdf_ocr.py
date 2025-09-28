"""
PDF OCR utility for extracting text from PDF files using OCR.
Optimized for processing thousands of PDFs efficiently and accurately.
"""
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFOCR:
    """PDF OCR utility for extracting text from PDF files."""
    
    def __init__(self, tesseract_path: Optional[str] = None, 
                 max_workers: int = 4, dpi: int = 300):
        """
        Initialize PDF OCR utility.
        
        Args:
            tesseract_path: Path to tesseract executable (if not in PATH)
            max_workers: Maximum number of threads for parallel processing
            dpi: Default DPI for image conversion
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.max_workers = max_workers
        self.default_dpi = dpi
        
        # Verify tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is available")
        except Exception as e:
            logger.error(f"Tesseract OCR not found: {e}")
            raise
    
    def preprocess_image(self, image: Image.Image, remove_watermarks: bool = True) -> Image.Image:
        """
        Preprocess image for better OCR accuracy and watermark removal.
        
        Args:
            image: PIL Image object
            remove_watermarks: Whether to attempt watermark removal
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            if remove_watermarks:
                # Advanced watermark removal techniques
                cv_image = self._remove_watermarks(cv_image)
            
            # Image enhancement for better OCR
            cv_image = self._enhance_for_ocr(cv_image)
            
            # Convert back to PIL
            image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            return image
    
    def _remove_watermarks(self, cv_image: np.ndarray) -> np.ndarray:
        """
        Remove watermarks and background noise from image.
        
        Args:
            cv_image: OpenCV image array
            
        Returns:
            Processed image with watermarks removed
        """
        try:
            # Convert to grayscale for processing
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Adaptive thresholding to separate text from background
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Remove small noise
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            # Convert back to 3-channel
            result = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
            
            return result
            
        except Exception as e:
            logger.warning(f"Watermark removal failed: {e}")
            return cv_image
    
    def _enhance_for_ocr(self, cv_image: np.ndarray) -> np.ndarray:
        """
        Enhance image for better OCR accuracy.
        
        Args:
            cv_image: OpenCV image array
            
        Returns:
            Enhanced image
        """
        try:
            # Convert to LAB color space for better processing
            lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels back
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            # Sharpen the image
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            return sharpened
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return cv_image
    
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
    
    def ocr_image(self, image: Image.Image, config: str = "--psm 6", 
                  remove_watermarks: bool = True) -> str:
        """
        Perform OCR on a single image with preprocessing.
        
        Args:
            image: PIL Image object
            config: Tesseract configuration string
            remove_watermarks: Whether to remove watermarks
            
        Returns:
            Extracted text
        """
        try:
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(image, remove_watermarks)
            
            # Perform OCR with multiple configurations for better accuracy
            configs = [config, "--psm 3", "--psm 6"]
            best_text = ""
            best_confidence = 0
            
            for cfg in configs:
                try:
                    # Get text and confidence
                    data = pytesseract.image_to_data(processed_image, config=cfg, output_type=pytesseract.Output.DICT)
                    text = pytesseract.image_to_string(processed_image, config=cfg).strip()
                    
                    # Calculate average confidence
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    if avg_confidence > best_confidence:
                        best_confidence = avg_confidence
                        best_text = text
                        
                except Exception as e:
                    logger.warning(f"OCR config {cfg} failed: {e}")
                    continue
            
            return best_text if best_text else pytesseract.image_to_string(processed_image, config=config).strip()
            
        except Exception as e:
            logger.error(f"Error performing OCR on image: {e}")
            return ""
    
    def ocr_pdf(self, pdf_path: str, dpi: int = 300, config: str = "--psm 6", 
                remove_watermarks: bool = True, parallel: bool = True) -> List[Dict[str, any]]:
        """
        Perform OCR on entire PDF file with parallel processing.
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion
            config: Tesseract configuration
            remove_watermarks: Whether to remove watermarks
            parallel: Whether to use parallel processing
            
        Returns:
            List of dictionaries with page info and extracted text
        """
        try:
            logger.info(f"Starting OCR for PDF: {pdf_path}")
            start_time = time.time()
            
            # Convert PDF to images
            images = self.pdf_to_images(pdf_path, dpi)
            
            if parallel and len(images) > 1:
                results = self._ocr_pages_parallel(images, config, remove_watermarks)
            else:
                results = self._ocr_pages_sequential(images, config, remove_watermarks)
            
            processing_time = time.time() - start_time
            logger.info(f"OCR completed for {len(images)} pages in {processing_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Error performing OCR on PDF: {e}")
            raise
    
    def _ocr_pages_parallel(self, images: List[Image.Image], config: str, 
                           remove_watermarks: bool) -> List[Dict[str, any]]:
        """Process pages in parallel for better performance."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all pages for processing
            future_to_page = {
                executor.submit(self.ocr_image, image, config, remove_watermarks): i 
                for i, image in enumerate(images)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    text = future.result()
                    results.append({
                        'page_number': page_num + 1,
                        'text': text,
                        'word_count': len(text.split()),
                        'character_count': len(text)
                    })
                    logger.info(f"Completed page {page_num + 1}")
                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1}: {e}")
                    results.append({
                        'page_number': page_num + 1,
                        'text': "",
                        'word_count': 0,
                        'character_count': 0
                    })
        
        # Sort results by page number
        results.sort(key=lambda x: x['page_number'])
        return results
    
    def _ocr_pages_sequential(self, images: List[Image.Image], config: str, 
                             remove_watermarks: bool) -> List[Dict[str, any]]:
        """Process pages sequentially."""
        results = []
        
        for page_num, image in enumerate(images):
            logger.info(f"Processing page {page_num + 1}/{len(images)}")
            
            # Perform OCR on this page
            text = self.ocr_image(image, config, remove_watermarks)
            
            results.append({
                'page_number': page_num + 1,
                'text': text,
                'word_count': len(text.split()),
                'character_count': len(text)
            })
        
        return results
    
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


    def batch_ocr_pdfs(self, pdf_directory: str, output_directory: str, 
                      dpi: int = 300, remove_watermarks: bool = True) -> Dict[str, any]:
        """
        Process multiple PDFs in a directory for batch processing.
        
        Args:
            pdf_directory: Directory containing PDF files
            output_directory: Directory to save OCR results
            dpi: DPI for image conversion
            remove_watermarks: Whether to remove watermarks
            
        Returns:
            Summary of batch processing results
        """
        try:
            import glob
            
            # Find all PDF files
            pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
            
            if not pdf_files:
                logger.warning(f"No PDF files found in {pdf_directory}")
                return {"processed": 0, "failed": 0, "total": 0}
            
            # Create output directory if it doesn't exist
            os.makedirs(output_directory, exist_ok=True)
            
            logger.info(f"Starting batch OCR for {len(pdf_files)} PDF files")
            start_time = time.time()
            
            processed = 0
            failed = 0
            
            for pdf_file in pdf_files:
                try:
                    # Generate output filename
                    base_name = os.path.splitext(os.path.basename(pdf_file))[0]
                    output_file = os.path.join(output_directory, f"{base_name}_ocr.txt")
                    
                    # Process PDF
                    results = self.ocr_pdf(pdf_file, dpi, remove_watermarks=remove_watermarks)
                    
                    # Save results
                    self.save_ocr_results(results, output_file)
                    
                    processed += 1
                    logger.info(f"✅ Processed: {os.path.basename(pdf_file)}")
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Failed: {os.path.basename(pdf_file)} - {e}")
            
            total_time = time.time() - start_time
            avg_time = total_time / len(pdf_files) if pdf_files else 0
            
            summary = {
                "processed": processed,
                "failed": failed,
                "total": len(pdf_files),
                "total_time": total_time,
                "avg_time_per_pdf": avg_time
            }
            
            logger.info(f"Batch processing completed: {processed}/{len(pdf_files)} successful")
            logger.info(f"Total time: {total_time:.2f}s, Average: {avg_time:.2f}s per PDF")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise


def ocr_pdf_file(pdf_path: str, output_path: Optional[str] = None, 
                dpi: int = 300, tesseract_path: Optional[str] = None,
                remove_watermarks: bool = True, parallel: bool = True) -> List[Dict[str, any]]:
    """
    Convenience function to OCR a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Optional path to save results
        dpi: DPI for image conversion
        tesseract_path: Path to tesseract executable
        remove_watermarks: Whether to remove watermarks
        parallel: Whether to use parallel processing
        
    Returns:
        OCR results
    """
    ocr = PDFOCR(tesseract_path)
    results = ocr.ocr_pdf(pdf_path, dpi, remove_watermarks=remove_watermarks, parallel=parallel)
    
    if output_path:
        ocr.save_ocr_results(results, output_path)
    
    return results


def batch_ocr_directory(pdf_directory: str, output_directory: str, 
                       dpi: int = 300, remove_watermarks: bool = True,
                       tesseract_path: Optional[str] = None) -> Dict[str, any]:
    """
    Convenience function for batch processing multiple PDFs.
    
    Args:
        pdf_directory: Directory containing PDF files
        output_directory: Directory to save OCR results
        dpi: DPI for image conversion
        remove_watermarks: Whether to remove watermarks
        tesseract_path: Path to tesseract executable
        
    Returns:
        Summary of batch processing results
    """
    ocr = PDFOCR(tesseract_path)
    return ocr.batch_ocr_pdfs(pdf_directory, output_directory, dpi, remove_watermarks)


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
