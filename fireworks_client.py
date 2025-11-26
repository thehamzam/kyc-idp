"""Fireworks AI client for document extraction."""
import os
import base64
from openai import OpenAI
from models import ExtractionResult

FIREWORKS_URL = "https://api.fireworks.ai/inference/v1"
MODEL = "accounts/fireworks/models/llama4-scout-instruct-basic"

PROMPT = """Look at this identity document image carefully.

READ THE ACTUAL TEXT visible and extract real information. DO NOT use placeholder data.
If you cannot read a field, use null.

Return JSON only:
{
  "name": "full name on document",
  "date_of_birth": "YYYY-MM-DD format",
  "document_number": "document/license number",
  "document_type": "passport or license",
  "expiry_date": "YYYY-MM-DD or null",
  "nationality": "country or null",
  "address": "address or null",
  "sex": "M or F or null"
}"""


class ExtractionError(Exception):
    """Extraction failed."""
    pass


def get_client() -> OpenAI:
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        raise ExtractionError("FIREWORKS_API_KEY not set")
    return OpenAI(api_key=api_key, base_url=FIREWORKS_URL)


def extract_document(image_data: bytes, content_type: str = "image/jpeg") -> ExtractionResult:
    """Extract info from document image using Fireworks AI."""
    client = get_client()
    b64 = base64.b64encode(image_data).decode('utf-8')
    data_url = f"data:{content_type};base64,{b64}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            max_tokens=1024,
            temperature=0.1
        )
        return ExtractionResult.from_response(response.choices[0].message.content)
    except Exception as e:
        raise ExtractionError(f"Extraction failed: {e}")


def check_api() -> tuple[bool, str]:
    """Check if API is configured."""
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        return False, "FIREWORKS_API_KEY not set"
    if len(api_key) < 10:
        return False, "API key appears invalid"
    return True, "OK"
