import pytest
import os
from pathlib import Path


@pytest.mark.integration
class TestPdfExtraction:
    """Integration tests that require OpenAI API key."""

    @pytest.fixture
    def example_pdf_bytes(self):
        pdf_path = Path(__file__).parent / "example_offer.pdf"
        if not pdf_path.exists():
            pytest.skip("example_offer.pdf not found")
        return pdf_path.read_bytes()

    @pytest.fixture
    def skip_without_api_key(self):
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

    def test_extract_text_from_pdf(self, example_pdf_bytes):
        from extraction import extract_text_from_pdf
        
        text = extract_text_from_pdf(example_pdf_bytes)
        
        assert "Nimbus Tech Solutions" in text
        assert "DE289456123" in text
        assert "Anna Müller" in text
        assert "Cloud Storage" in text

    def test_full_extraction_pipeline(self, example_pdf_bytes, skip_without_api_key):
        from extraction import extract_text_from_pdf, extract_offer_data
        
        text = extract_text_from_pdf(example_pdf_bytes)
        result = extract_offer_data(text)
        
        assert result.get("vendor_name") is not None
        assert "Nimbus" in result["vendor_name"] or "nimbus" in result["vendor_name"].lower()
        
        assert result.get("vat_id") == "DE289456123"
        
        assert result.get("order_lines") is not None
        assert len(result["order_lines"]) == 4
        
        assert result.get("stated_total_cost") == 3950.0 or result.get("stated_total_cost") == 3950
        
        line_descriptions = [line["description"].lower() for line in result["order_lines"]]
        assert any("cloud" in desc for desc in line_descriptions)
        assert any("dashboard" in desc or "intelligence" in desc for desc in line_descriptions)

    def test_commodity_classification(self, example_pdf_bytes, skip_without_api_key):
        from extraction import extract_text_from_pdf, extract_offer_data, classify_commodity_group
        
        text = extract_text_from_pdf(example_pdf_bytes)
        result = extract_offer_data(text)
        
        classification = classify_commodity_group(
            title=result.get("title", "IT Services"),
            order_lines=result.get("order_lines", []),
            vendor_name=result.get("vendor_name", ""),
            department=result.get("department", "")
        )
        
        assert classification.get("commodity_group_id") is not None
        assert classification.get("commodity_group_id") in ["029", "030", "031"]
        assert classification.get("confidence", 0) > 0.5
