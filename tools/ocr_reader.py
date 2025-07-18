import pytesseract
from PIL import Image
import cv2
import os

# Set Tesseract executable path (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def extract_text_from_image(image_path: str) -> str:
    try:
        image = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding to clean noise (optional but useful)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # OCR with English + Bangla
        text = pytesseract.image_to_string(thresh, lang='eng+ben')

        return text.strip()

    except Exception as e:
        print(f"[OCR Error] {e}")
        return "⚠️ OCR failed. Please try again with a clearer image."
