import os
import logging
from typing import Dict, List
import pypdf
from PIL import Image
import fitz  # PyMuPDF
import io
import cv2
import numpy as np
import easyocr

logger = logging.getLogger(__name__)

# Thai Unicode range: U+0E00 to U+0E7F
THAI_UNICODE_START = 0x0E00
THAI_UNICODE_END = 0x0E7F


class PDFExtractor:
    """
    PDF text extractor with Thai language support.
    Tries text extraction first, falls back to OCR for scanned PDFs.
    """
    
    def __init__(self):
        self.min_text_length = 10  # Minimum text length to consider valid
        self.thai_ratio_threshold = 0.1  # Minimum ratio of Thai characters
        self.reader = None  # Lazy load EasyOCR reader
        
    def _get_ocr_reader(self):
        if self.reader is None:
            logger.info("Initializing EasyOCR reader (Thai + English)...")
            self.reader = easyocr.Reader(['th', 'en'], gpu=False)
        return self.reader

    def _preprocess_image(self, img_pil: Image.Image) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy.
        - Grayscale conversion for Deep Learning OCR
        """
        img_np = np.array(img_pil)
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
        return gray

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
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            pages = []
            
            # Configure resolution from env (default 300 DPI for high accuracy)
            try:
                dpi = int(os.getenv("OCR_DPI", "300"))
            except ValueError:
                dpi = 300
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # Get the EasyOCR reader
            reader = self._get_ocr_reader()
            
            for page_num in range(page_count):
                page = doc[page_num]
                
                # Render page to image at high DPI
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Preprocess image using OpenCV
                processed_img = self._preprocess_image(img)
                
                # Run OCR with EasyOCR
                try:
                    ocr_results = reader.readtext(processed_img)
                    text = self._reconstruct_text_layout(ocr_results)
                except Exception as e:
                    logger.error(f"EasyOCR error: {e}")
                    raise Exception(f"Failed to run EasyOCR: {str(e)}")
                
                pages.append(text if text else "")
                logger.info(f"OCR completed for page {page_num + 1}/{page_count}")
            
            doc.close()
            
            combined_text = "\n\n".join(pages)
            
            return {
                "text": combined_text,
                "pages": pages,
                "page_count": page_count
            }
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise

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
