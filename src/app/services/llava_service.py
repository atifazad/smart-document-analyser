import os
import requests
import base64
from typing import Any, Dict

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLAVA_MODEL = os.getenv("LLAVA_MODEL", "llava:latest")

class LLaVAServiceError(Exception):
    pass

def analyze_image_with_llava(image_path: str, prompt: str = None, timeout: int = 60) -> Dict[str, Any]:
    if prompt is None:
        # Optimized, focused prompt for faster processing
        prompt = """Analyze this document and provide:

1. Document type (invoice, form, report, notes, receipt, letter)
2. Key text content and important details
3. Visual elements (tables, charts, diagrams)
4. Main purpose and context

Be concise and structured."""
    
    url = f"{OLLAMA_HOST}/api/generate"
    try:
        with open(image_path, "rb") as img_file:
            img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        payload = {
            "model": LLAVA_MODEL,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=timeout)
        try:
            response.raise_for_status()
        except requests.HTTPError as http_err:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise LLaVAServiceError(f"LLaVA/Ollama call failed: {http_err} | Detail: {error_detail}")
        result = response.json()
        return result
    except Exception as e:
        raise LLaVAServiceError(f"LLaVA/Ollama call failed: {e}")

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