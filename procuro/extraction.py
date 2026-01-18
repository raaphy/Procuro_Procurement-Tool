import os
import io
import json
import base64
from openai import OpenAI
from pypdf import PdfReader
from dotenv import load_dotenv
from commodity_groups import get_commodity_groups_for_prompt

load_dotenv()

_client = None

# Toggle für Vision-Modus (True = GPT-4o mit Bildern, False = nur Text)
USE_VISION = os.getenv("USE_VISION", "true").lower() == "true"


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def pdf_to_images_base64(file_bytes: bytes) -> list[str]:
    """Konvertiert PDF-Seiten zu Base64-codierten PNG-Bildern."""
    try:
        import pymupdf
    except ImportError:
        raise ImportError("pymupdf benötigt für Vision-Modus: pip install pymupdf")
    
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        images.append(base64.b64encode(img_bytes).decode("utf-8"))
    doc.close()
    return images


def log_openai_request(messages: list, model: str):
    print("\n" + "=" * 60)
    print("🔵 OPENAI REQUEST")
    print("=" * 60)
    print(f"Model: {model}")
    for msg in messages:
        print(f"\n[{msg['role'].upper()}]:")
        print(msg['content'][:500] + "..." if len(msg['content']) > 500 else msg['content'])
    print("=" * 60 + "\n")


def log_openai_response(response):
    print("\n" + "=" * 60)
    print("🟢 OPENAI RESPONSE")
    print("=" * 60)
    print(response.choices[0].message.content)
    print("=" * 60 + "\n")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_offer_data_from_pdf(file_bytes: bytes, use_vision: bool = None) -> dict:
    """
    Extrahiert Angebotsdaten aus PDF.
    
    Args:
        file_bytes: PDF als Bytes
        use_vision: True=Vision+Text, False=nur Text, None=USE_VISION env var
    """
    if use_vision is None:
        use_vision = USE_VISION
    
    # Text immer extrahieren (auch für Vision als zusätzlicher Kontext)
    text = extract_text_from_pdf(file_bytes)
    
    if use_vision:
        images = pdf_to_images_base64(file_bytes)
        return extract_offer_data_vision(text, images)
    else:
        return extract_offer_data(text)

required_json_structure_offer = """Required JSON structure:
{
    "vendor_name": "string (the company or person sending the offer, not the recipient. leave blank if unknown)",
    "vat_id": "string (format: DE followed by 9 digits, e.g., DE123456789)",
    "department": "string (the department the offer is addressed to, not the one creating the offer. Leave blank if unknown)",
    "requestor_name": "string (the person the offer is addressed to, e.g. from salutation )",
    "title": "string (the offer title if explicitly stated, otherwise generate a concise descriptive title from the order lines, e.g. 'Adobe Software Licenses' or 'Office Furniture Order')",
    "currency": "string (3-letter currency code like EUR, USD, GBP, CHF - extract from currency symbols € $ £ or explicit mentions)",
    "order_lines": [
        {
            "description": "string",
            "unit_price": number,
            "quantity": number,
            "unit": "string (The unit of measure or quantity)",
            "stated_total_price": number (the total price as stated in the document for this line)
}
],
"stated_total_cost": number (the total cost of the entire offer as stated in the document)
}

If a field cannot be found, use null for strings/numbers and empty array for order_lines.
Extract prices as numbers without currency symbols.
For requestor_name: Look for salutations, "Attention:", "To:", or similar addressing patterns.
For title: If no explicit offer title exists, create a short meaningful title summarizing the main items being offered.
For currency: Default to EUR if not explicitly stated but Euro symbols (€) are used.
"""

def extract_offer_data(text: str) -> dict:
    system_prompt = """You are an expert at extracting structured data from vendor offers.
Extract the following information from the provided text and return it as valid JSON only.
Do not include any explanation, only the JSON object.

""" + required_json_structure_offer

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract data from this vendor offer:\n\n{text}"}
    ]
    
    log_openai_request(messages, "gpt-5-mini")

    response = get_client().chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        response_format={"type": "json_object"}
    )

    log_openai_response(response)

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {}


def classify_commodity_group(title: str, order_lines: list, vendor_name: str = "", department: str = "") -> dict:
    commodity_list = get_commodity_groups_for_prompt()
    
    order_lines_text = "\n".join([f"- {line.get('description', '')}" for line in order_lines])
    
    system_prompt = f"""You are an expert at classifying procurement requests into commodity groups.
Based on the provided information, select the most appropriate commodity group from this list:

{commodity_list}

Return your response as valid JSON only with this structure:
{{
    "commodity_group_id": "string (the 3-digit ID like 001, 031, etc.)",
    "confidence": number (0.0 to 1.0),
    "rationale": "string (brief explanation)"
}}
"""

    user_content = f"""Classify this procurement request:
Title: {title}
Vendor: {vendor_name}
Department: {department}
Order Lines:
{order_lines_text}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    log_openai_request(messages, "gpt-5-mini")

    response = get_client().chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        response_format={"type": "json_object"}
    )

    log_openai_response(response)

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"commodity_group_id": "009", "confidence": 0.0, "rationale": "Classification failed"}


def extract_offer_data_vision(text: str, images_base64: list[str]) -> dict:
    print("Extended extraction ###############################")
    """
    Extrahiert Angebotsdaten mit GPT-4o Vision (Text + Bilder).
    Nutzt extrahierten Text als zusätzlichen Kontext.
    """
    system_prompt = """You are an expert at extracting structured data from vendor offers.
You receive both the document images AND extracted text (which may be incomplete for scanned documents).
Use BOTH sources to extract accurate information - the images show the actual document layout.

Extract the following information and return it as valid JSON only.
Do not include any explanation, only the JSON object.

""" + required_json_structure_offer

    # Baue multimodalen Content: Text + alle Bilder
    user_content = [
        {
            "type": "text",
            "text": f"Extract data from this vendor offer.\n\nExtracted text (may be incomplete):\n{text}\n\nDocument images follow:"
        }
    ]
    
    for img_b64 in images_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_b64}",
                "detail": "high"
            }
        })

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    # TODO: create debugging flag that can be switched off
    print("\n" + "=" * 60)
    print("🔵 OPENAI VISION REQUEST")
    print("=" * 60)
    print(f"Model: gpt-4o")
    print(f"Images: {len(images_base64)} pages")
    print(f"Text length: {len(text)} chars")
    print("=" * 60 + "\n")

    response = get_client().chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"}
    )
    # TODO: create debugging flag that can be switched off
    log_openai_response(response)

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {}
