import os
from typing import List
from pdf2image import convert_from_path
from PIL import Image

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
