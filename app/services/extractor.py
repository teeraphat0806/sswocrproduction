import gc
import os
import logging
import threading
from typing import Dict
import pypdf
import fitz  # PyMuPDF
import numpy as np

logger = logging.getLogger(__name__)

# Thai Unicode range: U+0E00 to U+0E7F
THAI_UNICODE_START = 0x0E00
THAI_UNICODE_END = 0x0E7F


class PDFExtractor:
    """
    PDF text extractor with Thai language support.
    Tries text extraction first, falls back to OCR for scanned PDFs.
    """

    _shared_reader = None
    _reader_lock = threading.Lock()
    _ocr_lock = threading.Lock()
    
    def __init__(self):
        self.min_text_length = 10  # Minimum text length to consider valid
        self.thai_ratio_threshold = 0.1  # Minimum ratio of Thai characters
        
    def _get_ocr_reader(self):
        if PDFExtractor._shared_reader is None:
            with PDFExtractor._reader_lock:
                if PDFExtractor._shared_reader is None:
                    import easyocr  # Lazy import to avoid loading PyTorch until OCR is actually needed
                    logger.info("Initializing EasyOCR reader (Thai + English)...")
                    PDFExtractor._shared_reader = easyocr.Reader(['th', 'en'], gpu=False)
        return PDFExtractor._shared_reader

    def _preprocess_image(self, img_pil) -> np.ndarray:
        """
        Preprocess PIL image to grayscale numpy array for OCR.
        Kept for compatibility; _extract_with_ocr renders grayscale directly via PyMuPDF.
        """
        return np.array(img_pil.convert("L"))

    def _reconstruct_text_layout(self, ocr_results) -> str:
        """
        Reconstruct text layout from EasyOCR results to preserve tabular structure.
        Groups text boxes on the same horizontal line and sorts them from left to right.
        """
        if not ocr_results:
            return ""
            
        items = []
        for bbox, text, conf in ocr_results:
            if not text or not text.strip():
                continue
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            height = y_max - y_min
            center_y = y_min + height / 2
            
            items.append({
                "text": text,
                "x_min": x_min,
                "x_max": x_max,
                "y_min": y_min,
                "y_max": y_max,
                "height": height,
                "center_y": center_y
            })
            
        if not items:
            return ""
            
        # Group items into lines
        lines = []
        items.sort(key=lambda x: x["center_y"])
        
        while items:
            current_item = items.pop(0)
            line = [current_item]
            remaining_items = []
            tolerance = current_item["height"] * 0.4
            
            for item in items:
                y_overlap = min(current_item["y_max"], item["y_max"]) - max(current_item["y_min"], item["y_min"])
                min_height = min(current_item["height"], item["height"])
                
                if y_overlap > 0.4 * min_height or abs(item["center_y"] - current_item["center_y"]) < tolerance:
                    line.append(item)
                else:
                    remaining_items.append(item)
            
            line.sort(key=lambda x: x["x_min"])
            lines.append(line)
            items = remaining_items
            
        # Sort lines by their average Y coordinate (top to bottom)
        lines.sort(key=lambda l: sum(item["center_y"] for item in l) / len(l))
        
        # Build text output
        output_lines = []
        for line in lines:
            line_str = "  ".join(item["text"] for item in line)
            output_lines.append(line_str)
            
        return "\n".join(output_lines)
    
    # ฟังก์ชันหลักที่เรียกใช้ในการสกัดข้อความจาก PDF โดยจะพยายามใช้การสกัดข้อความแบบปกติก่อน ถ้าไม่สำเร็จหรือข้อความไม่ดีพอ จะใช้ OCR แทน
    def extract(self, pdf_path: str) -> Dict:
        """
        Extract text from PDF using text extraction or OCR.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with:
                - text: Combined text from all pages
                - pages: List of text from each page
                - page_count: Number of pages
                - method: 'pdf_text' or 'ocr'
        """
        logger.info(f"Starting extraction for: {pdf_path}")
        
        # Try text extraction first
        text_result = self._extract_text(pdf_path)
        
        if self._is_valid_extraction(text_result["text"]):
            logger.info("Text extraction successful")
            return {
                "text": text_result["text"],
                "pages": text_result["pages"],
                "page_count": text_result["page_count"],
                "method": "pdf_text"
            }
        
        # Fallback to OCR
        logger.info("Text extraction insufficient, falling back to OCR")
        ocr_result = self._extract_with_ocr(pdf_path)
        
        return {
            "text": ocr_result["text"],
            "pages": ocr_result["pages"],
            "page_count": ocr_result["page_count"],
            "method": "ocr"
        }
    # pypdf → อ่านข้อความจาก PDF โดยตรง ซึ่งจะได้ผลดีสำหรับ PDF ที่มีข้อความจริง (ไม่ใช่สแกน) และรองรับภาษาไทยและภาษาอังกฤษ
    def _extract_text(self, pdf_path: str) -> Dict:
        """
        Extract text using pypdf.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with text, pages, and page_count
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                page_count = len(pdf_reader.pages)
                pages = []
                
                for page_num in range(page_count):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    pages.append(text if text else "")
                
                combined_text = "\n\n".join(pages)
                
                return {
                    "text": combined_text,
                    "pages": pages,
                    "page_count": page_count
                }
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                "text": "",
                "pages": [],
                "page_count": 0
            }
        
    #pytesseract → อ่านข้อความจากรูปภาพ โดยใช้ Tesseract OCR ซึ่งรองรับภาษาไทยและภาษาอังกฤษ
    def _extract_with_ocr(self, pdf_path: str) -> Dict:
        """
        Extract text using OCR with EasyOCR (Thai and English).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with text, pages, and page_count
        """
        # Configure resolution and canvas size from env to balance accuracy and RAM
        try:
            dpi = int(os.getenv("OCR_DPI", "200"))
        except ValueError:
            dpi = 200

        try:
            canvas_size = int(os.getenv("OCR_CANVAS_SIZE", "1280"))
        except ValueError:
            canvas_size = 1280

        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        # Get shared EasyOCR reader (lazy-loaded singleton)
        reader = self._get_ocr_reader()
        pages = []

        try:
            with fitz.open(pdf_path) as doc:
                page_count = len(doc)

                for page_num in range(page_count):
                    page = doc[page_num]

                    # Render page directly to grayscale pixmap and convert to numpy without PNG/PIL/OpenCV copies
                    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY, alpha=False)
                    processed_img = np.frombuffer(
                        pix.samples, dtype=np.uint8
                    ).reshape(pix.height, pix.width).copy()
                    del pix

                    # Run OCR with EasyOCR (serialized via lock to prevent concurrent peak RAM spikes)
                    try:
                        with PDFExtractor._ocr_lock:
                            ocr_results = reader.readtext(
                                processed_img,
                                canvas_size=canvas_size,
                            )
                        text = self._reconstruct_text_layout(ocr_results)
                    except Exception as e:
                        logger.error(f"EasyOCR error: {e}")
                        raise Exception(f"Failed to run EasyOCR: {str(e)}")
                    finally:
                        del processed_img

                    pages.append(text if text else "")
                    logger.info(f"OCR completed for page {page_num + 1}/{page_count}")

            combined_text = "\n\n".join(pages)

            return {
                "text": combined_text,
                "pages": pages,
                "page_count": page_count
            }
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
        finally:
            gc.collect()

    # ใช้ตรวจว่า:“text ที่ได้จาก pypdf ดีพอหรือยัง” ถ้าไม่ดีพอ (เช่น มีแต่ตัวอักษรภาษาอังกฤษ หรือมีข้อความน้อยเกินไป) ก็จะไปใช้ OCR แทน
    def _is_valid_extraction(self, text: str) -> bool:
        """
        Check if extracted text is valid Thai text.
        
        Args:
            text: Extracted text
            
        Returns:
            True if text appears valid, False otherwise
        """
        if not text or len(text.strip()) < self.min_text_length:
            logger.debug("Text too short or empty")
            return False
        
        # Count Thai characters
        thai_count = sum(
            1 for char in text
            if THAI_UNICODE_START <= ord(char) <= THAI_UNICODE_END
        )
        
        # Count total alphanumeric characters
        total_chars = sum(1 for char in text if char.isalnum() or THAI_UNICODE_START <= ord(char) <= THAI_UNICODE_END)
        
        if total_chars == 0:
            logger.debug("No alphanumeric characters found")
            return False
        
        thai_ratio = thai_count / total_chars
        logger.debug(f"Thai character ratio: {thai_ratio:.2f} ({thai_count}/{total_chars})")
        
        # Check if we have enough Thai characters
        if thai_ratio >= self.thai_ratio_threshold:
            return True
        
        logger.debug(f"Thai ratio {thai_ratio:.2f} below threshold {self.thai_ratio_threshold}")
        return False
