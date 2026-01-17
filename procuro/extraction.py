import os
import json
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from commodity_groups import get_commodity_groups_for_prompt

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


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
    import io
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_offer_data(text: str) -> dict:
    system_prompt = """You are an expert at extracting structured data from vendor offers.
Extract the following information from the provided text and return it as valid JSON only.
Do not include any explanation, only the JSON object.

Required JSON structure:
{
    "vendor_name": "string (the company or person sending the offer)",
    "vat_id": "string (format: DE followed by 9 digits, e.g., DE123456789)",
    "department": "string (the department the offer is addressed to)",
    "requestor_name": "string (the person the offer is addressed to, e.g. from salutation like 'Dear Mr. Smith' or 'Sehr geehrter Herr Müller')",
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
