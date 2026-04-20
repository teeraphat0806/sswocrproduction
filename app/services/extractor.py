import os
import logging
from typing import Dict, List
import pypdf
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io

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
        Extract text using OCR with Tesseract (Thai language).
        
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
            
            # Configure Tesseract for Thai
            # psm 3 = Fully automatic page segmentation (default)
            # oem 3 = Default, based on what is available (LSTM if available)
            custom_config = r'--oem 3 --psm 3'
            
            for page_num in range(page_count):
                page = doc[page_num]
                
                # Render page to image
                # Use higher DPI for better OCR accuracy
                zoom = 2.0  # 2x zoom = 144 DPI (default is 72 DPI)
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Run OCR with Thai language
                try:
                    text = pytesseract.image_to_string(
                        img,
                        lang='tha+eng',  # Thai + English
                        config=custom_config
                    )
                except pytesseract.TesseractNotFoundError:
                    logger.error("Tesseract not found. Please install Tesseract OCR.")
                    raise Exception(
                        "Tesseract OCR is not installed. "
                        "Please install Tesseract and Thai language data (tha)."
                    )
                
                pages.append(text if text else "")
                logger.debug(f"OCR completed for page {page_num + 1}/{page_count}")
            
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
