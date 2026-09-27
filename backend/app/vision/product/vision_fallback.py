from __future__ import annotations

import base64
import os
from typing import Any

from groq import Groq

from app.core.config import get_settings


VISION_PROMPT = """You are a BIS label analysis expert. Analyze this product label/image and extract the following information in JSON format:

{
  "is_number": "The Indian Standard (IS) number if visible (e.g., IS 14543, IS 302, IS 16000)",
  "licence_number": "The BIS licence number if visible (format: CM/L-XXXXXX)",
  "mrp": "Maximum Retail Price if visible (e.g., ₹150, Rs. 150)",
  "quantity": "Net quantity/weight if visible (e.g., 50 kg, 1 L, 100 g)",
  "manufacturer": "Manufacturer name if visible",
  "product_name": "Product name/brand if visible",
  "batch": "Batch/Lot number if visible",
  "hsn_code": "HSN/SAC code if visible",
  "raw_text": "All visible text from the label"
}

Only return valid JSON. If a field is not visible, use null. Be precise - only extract what is actually visible in the image."""


def analyze_with_vision(image_path: str) -> dict[str, Any]:
    """Use Groq vision model to analyze the product label image."""
    settings = get_settings()
    
    api_key = settings.openai_api_key or settings.groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "No API key configured for vision fallback"}
    
    client = Groq(api_key=api_key)
    
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    try:
        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {"error": f"Vision analysis failed: {str(e)}"}


def is_meaningful_extraction(extracted: dict) -> bool:
    """Check if OCR extracted meaningful information."""
    key_fields = ["is_number", "licence_number", "manufacturer", "product_name"]
    return any(extracted.get(field) for field in key_fields)