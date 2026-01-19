"""
Integration tests with real OpenAI API.
Run with: pytest tests/test_extraction_openai.py -m integration
Requires: OPENAI_API_KEY environment variable
"""

import os
import pytest
from pathlib import Path

from backend.extraction import extract_offer_data_from_pdf, classify_commodity_group


pytestmark = pytest.mark.integration


EXPECTED_VENDOR_NAME = "Nimbus Tech Solutions GmbH"
EXPECTED_VAT_ID = "DE289456123"
EXPECTED_CURRENCY = "EUR"
EXPECTED_TOTAL_COST = 3950.0
EXPECTED_ORDER_LINE_COUNT = 4

EXPECTED_ORDER_LINES = [
    {"description_contains": "Cloud Storage", "unit_price": 120.0, "quantity": 10, "total": 1200.0},
    {"description_contains": "Business Intelligence", "unit_price": 450.0, "quantity": 3, "total": 1350.0},
    {"description_contains": "Data Security", "unit_price": 300.0, "quantity": 2, "total": 600.0},
    {"description_contains": "Training", "unit_price": 800.0, "quantity": 1, "total": 800.0},
]


@pytest.fixture
def example_pdf_bytes():
    pdf_path = Path(__file__).parent / "example_offer.pdf"
    with open(pdf_path, "rb") as f:
        return f.read()


def skip_if_no_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")


class TestOpenAIExtractionIntegration:
    def test_full_pdf_extraction(self, example_pdf_bytes):
        """Single test for all extraction checks to minimize API calls."""
        skip_if_no_api_key()
        
        result = extract_offer_data_from_pdf(example_pdf_bytes)
        
        # Vendor name
        assert result.get("vendor_name") is not None
        assert "Nimbus" in result["vendor_name"] or "Tech" in result["vendor_name"]
        
        # VAT ID
        assert result.get("vat_id") == EXPECTED_VAT_ID
        
        # Currency
        assert result.get("currency") in ["EUR", "€"]
        
        # Total cost
        stated_total = result.get("stated_total_cost")
        assert stated_total is not None
        assert abs(stated_total - EXPECTED_TOTAL_COST) < 10
        
        # Order lines count
        order_lines = result.get("order_lines", [])
        assert len(order_lines) == EXPECTED_ORDER_LINE_COUNT
        
        # Order lines prices sum
        sum_calculated = sum(
            line.get("unit_price", 0) * line.get("quantity", 0)
            for line in order_lines
        )
        assert abs(sum_calculated - EXPECTED_TOTAL_COST) < 10
        
        # Structure validation
        assert "vendor_name" in result
        assert "vat_id" in result
        assert "currency" in result
        assert "order_lines" in result
        assert "stated_total_cost" in result
        
        for line in order_lines:
            assert "description" in line
            assert "unit_price" in line
            assert "quantity" in line


class TestOpenAIClassificationIntegration:
    def test_classify_it_software(self):
        skip_if_no_api_key()
        
        result = classify_commodity_group(
            title="Cloud & Analytics Software Bundle",
            order_lines=[
                {"description": "Cloud Storage Enterprise Plan"},
                {"description": "Business Intelligence Dashboard License"},
            ],
            vendor_name="Nimbus Tech Solutions GmbH",
            department="IT",
        )
        
        assert result.get("commodity_group_id") is not None
        assert result.get("confidence", 0) > 0.5
        assert "rationale" in result

    def test_classify_returns_valid_id(self):
        skip_if_no_api_key()
        
        result = classify_commodity_group(
            title="Office Furniture",
            order_lines=[{"description": "Desk"}, {"description": "Chair"}],
        )
        
        commodity_id = result.get("commodity_group_id", "")
        assert len(commodity_id) == 3
        assert commodity_id.isdigit()
