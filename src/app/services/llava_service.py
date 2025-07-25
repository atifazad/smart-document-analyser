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
        prompt = """Analyze this document comprehensively and provide a structured analysis for downstream processing.

Please provide:

1. **Document Type**: Identify the type (invoice, form, report, notes, receipt, letter, etc.)

2. **Text Content**: Transcribe all readable text from the document, preserving formatting and structure

3. **Key Information**: Extract important details such as:
   - Dates, names, numbers, amounts
   - Contact information, addresses
   - Reference numbers, IDs
   - Important facts or data points

4. **Structure & Layout**: Describe the document organization:
   - Headers, sections, paragraphs
   - Lists, bullet points, numbered items
   - Columns, rows, formatting

5. **Visual Elements**: Identify and describe:
   - Tables, charts, graphs
   - Diagrams, images, logos
   - Handwriting style (if applicable)
   - Any visual components

6. **Context & Purpose**: Explain what this document is for and its main topic

Provide a comprehensive, structured response that captures all the above elements for effective downstream processing."""
    
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