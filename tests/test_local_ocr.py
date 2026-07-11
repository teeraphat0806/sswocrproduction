import unittest
from PIL import Image
import numpy as np
from app.services.extractor import PDFExtractor

class TestLocalOCR(unittest.TestCase):
    def setUp(self):
        self.extractor = PDFExtractor()

    def test_preprocess_image(self):
        # Create a dummy RGB image
        img = Image.new("RGB", (100, 100), color="white")
        processed = self.extractor._preprocess_image(img)
        
        # Output should be a numpy array representing a grayscale image
        self.assertIsInstance(processed, np.ndarray)
        self.assertEqual(len(processed.shape), 2)  # Grayscale should be 2D
        self.assertEqual(processed.shape, (100, 100))

    def test_reconstruct_text_layout(self):
        # Test case: 2 columns and 2 rows
        # Line 1: "Header Left" at y=10-20, "Header Right" at y=12-22
        # Line 2: "Item 1" at y=50-60, "100.00" at y=52-62
        
        ocr_results = [
            # bbox layout: [[x_tl, y_tl], [x_tr, y_tr], [x_br, y_br], [x_bl, y_bl]]
            ([[10, 10], [100, 10], [100, 20], [10, 20]], "Header Left", 0.95),
            ([[300, 12], [400, 12], [400, 22], [300, 22]], "Header Right", 0.95),
            ([[10, 50], [80, 50], [80, 60], [10, 60]], "Item 1", 0.95),
            ([[300, 52], [350, 52], [350, 62], [300, 62]], "100.00", 0.95),
        ]
        
        reconstructed = self.extractor._reconstruct_text_layout(ocr_results)
        
        # Verify both lines were reconstructed with double spaces between columns
        self.assertIn("Header Left  Header Right", reconstructed)
        self.assertIn("Item 1  100.00", reconstructed)
        
        # Verify line order (Line 1 should be before Line 2)
        lines = reconstructed.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].strip(), "Header Left  Header Right")
        self.assertEqual(lines[1].strip(), "Item 1  100.00")

    def test_empty_results(self):
        reconstructed = self.extractor._reconstruct_text_layout([])
        self.assertEqual(reconstructed, "")

if __name__ == "__main__":
    unittest.main()
