import os
from typing import List
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import cv2
import numpy as np

def convert_pdf_to_images(pdf_path: str, output_dir: str) -> List[str]:
    """
    Converts a PDF file to images (one per page) and saves them to output_dir.
    Returns a list of image file paths.
    """
    try:
        images = convert_from_path(pdf_path)
        output_paths = []
        for i, img in enumerate(images):
            out_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page{i+1}.png")
            img.save(out_path, "PNG")
            output_paths.append(out_path)
        return output_paths
    except Exception as e:
        raise RuntimeError(f"PDF to image conversion failed: {e}")

def validate_and_standardize_image(image_path: str, output_dir: str, target_format: str = "PNG", max_size: int = 2000) -> str:
    """
    Validates and standardizes an image: converts to target_format and resizes if too large.
    Returns the path to the standardized image.
    """
    try:
        with Image.open(image_path) as img:
            # Optionally resize if too large
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size))
            base = os.path.splitext(os.path.basename(image_path))[0]
            out_path = os.path.join(output_dir, f"{base}_std.{target_format.lower()}")
            img.convert("RGB").save(out_path, target_format)
            return out_path
    except Exception as e:
        raise RuntimeError(f"Image validation/standardization failed: {e}")

def enhance_image_for_handwriting(image_path: str, output_dir: str) -> str:
    """
    Enhances image specifically for handwritten text recognition.
    Applies contrast enhancement, noise reduction, and sharpening.
    """
    try:
        # Read image with OpenCV for better processing
        img = cv2.imread(image_path)
        if img is None:
            raise RuntimeError("Could not read image")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Apply slight sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Convert back to PIL Image
        enhanced_img = Image.fromarray(sharpened)
        
        # Save enhanced image
        base = os.path.splitext(os.path.basename(image_path))[0]
        out_path = os.path.join(output_dir, f"{base}_enhanced.png")
        enhanced_img.save(out_path, "PNG")
        
        return out_path
    except Exception as e:
        raise RuntimeError(f"Image enhancement failed: {e}")

def ocr_image_with_tesseract(image_path: str) -> str:
    """
    Extracts all visible text from an image using pytesseract OCR.
    Returns the extracted text as a string.
    Raises RuntimeError on failure.
    """
    try:
        with Image.open(image_path) as img:
            text = pytesseract.image_to_string(img)
            return text
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")

def ocr_handwritten_text(image_path: str) -> str:
    """
    Specialized OCR for handwritten text with optimized configuration.
    """
    try:
        with Image.open(image_path) as img:
            # Configure Tesseract for handwriting
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?()[]{}:;"\'-'
            
            # Try multiple PSM modes for better handwriting recognition
            psm_modes = [6, 8, 13]  # 6=uniform block, 8=single word, 13=raw line
            best_result = ""
            
            for psm in psm_modes:
                config = f'--oem 3 --psm {psm}'
                try:
                    result = pytesseract.image_to_string(img, config=config)
                    if len(result.strip()) > len(best_result.strip()):
                        best_result = result
                except Exception:
                    continue
            
            return best_result if best_result else pytesseract.image_to_string(img)
    except Exception as e:
        raise RuntimeError(f"Handwritten OCR failed: {e}")
