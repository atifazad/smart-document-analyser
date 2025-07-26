import os
import logging
import requests
import json
from typing import Dict, Any, Optional
from PIL import Image
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class LLaVAServiceError(Exception):
    """Custom exception for LLaVA service errors"""
    pass

def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize for faster processing (optional)
            max_size = 512
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)  # Reduced quality for speed
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return img_str
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {e}")
        raise LLaVAServiceError(f"Image encoding failed: {e}")

def analyze_image_with_llava(image_path: str, prompt: str = None, timeout: int = 60) -> Dict[str, Any]:
    """Analyze image using LLaVA model"""
    try:
        # Encode image
        image_base64 = encode_image_to_base64(image_path)
        
        # Prepare request
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        llava_model = os.getenv("LLAVA_MODEL", "llava:latest")
        
        if prompt is None:
            # Optimized, focused prompt for faster processing
            prompt = """Analyze this document and provide:
1. Document type (invoice, form, report, notes, receipt, letter)
2. Key text content and important details
3. Visual elements (tables, charts, diagrams)
4. Main purpose and context
Be concise and structured."""
        
        payload = {
            "model": llava_model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 200,  # Reduced for speed
                "stop": ["</s>", "```", "\n\n\n"]
            }
        }
        
        # Make request
        response = requests.post(
            f"{ollama_host}/api/generate",
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise LLaVAServiceError(f"LLaVA API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        return {
            "response": result.get("response", ""),
            "processing_time": result.get("total_duration", 0) / 1_000_000_000 if result.get("total_duration") else None,
            "model": llava_model
        }
        
    except requests.exceptions.Timeout:
        raise LLaVAServiceError(f"LLaVA request timed out after {timeout}s")
    except Exception as e:
        logger.error(f"LLaVA analysis failed: {e}")
        raise LLaVAServiceError(f"LLaVA analysis failed: {e}")

def analyze_image_with_llava_fast(image_path: str, timeout: int = 30) -> Dict[str, Any]:
    """Ultra-fast LLaVA analysis with minimal prompt for speed"""
    prompt = """Document type and key info only. Be brief."""
    return analyze_image_with_llava(image_path, prompt, timeout)

def analyze_image_with_llava_detailed(image_path: str, timeout: int = 90) -> Dict[str, Any]:
    """Detailed LLaVA analysis for important documents"""
    prompt = """Analyze this document comprehensively:
1. Document Type: Identify type (invoice, form, report, notes, receipt, letter)
2. Text Content: Extract all readable text
3. Key Information: Dates, names, numbers, amounts, contact info
4. Visual Elements: Tables, charts, diagrams, handwriting
5. Structure: Headers, sections, formatting
6. Purpose: What this document is for
Provide structured analysis."""
    return analyze_image_with_llava(image_path, prompt, timeout)

def analyze_image_with_llava_ultra_fast(image_path: str, timeout: int = 15) -> Dict[str, Any]:
    """Ultra-fast LLaVA analysis with minimal processing for maximum speed"""
    try:
        # Encode image with minimal processing
        image_base64 = encode_image_to_base64(image_path)
        
        # Prepare request with minimal settings
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        llava_model = os.getenv("LLAVA_MODEL", "llava:latest")
        
        payload = {
            "model": llava_model,
            "prompt": "Document type only. One word answer.",
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.0,  # Deterministic for speed
                "top_p": 0.1,
                "num_predict": 10,  # Very short response
                "stop": ["\n", ".", " "]
            }
        }
        
        # Make request
        response = requests.post(
            f"{ollama_host}/api/generate",
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise LLaVAServiceError(f"LLaVA API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        return {
            "response": result.get("response", ""),
            "processing_time": result.get("total_duration", 0) / 1_000_000_000 if result.get("total_duration") else None,
            "model": llava_model
        }
        
    except requests.exceptions.Timeout:
        raise LLaVAServiceError(f"LLaVA request timed out after {timeout}s")
    except Exception as e:
        logger.error(f"LLaVA analysis failed: {e}")
        raise LLaVAServiceError(f"LLaVA analysis failed: {e}") 