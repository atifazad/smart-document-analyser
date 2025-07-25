import os
import requests
import base64
from typing import Any, Dict

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLAVA_MODEL = os.getenv("LLAVA_MODEL", "llava:latest")

class LLaVAServiceError(Exception):
    pass

def analyze_image_with_llava(image_path: str, prompt: str = "Describe the visual elements and layout.", timeout: int = 60) -> Dict[str, Any]:
    """
    Calls Ollama's LLaVA model with the given image and prompt using /api/generate.
    Returns the parsed response as a dict.
    Raises LLaVAServiceError on failure.
    """
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