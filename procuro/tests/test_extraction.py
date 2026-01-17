import pytest
import json
from unittest.mock import patch, MagicMock


class TestExtractOfferData:
    @patch('extraction.client')
    def test_extract_offer_data_parses_valid_json(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "vendor_name": "Test Vendor",
            "vat_id": "DE987654321",
            "department": "IT",
            "requestor_name": "John Doe",
            "title": "Software Licenses",
            "currency": "EUR",
            "order_lines": [
                {
                    "description": "Adobe Photoshop",
                    "unit_price": 150,
                    "quantity": 10,
                    "unit": "licenses",
                    "stated_total_price": 1500
                }
            ],
            "stated_total_cost": 1500
        })
        mock_client.chat.completions.create.return_value = mock_response

        from extraction import extract_offer_data
        result = extract_offer_data("Sample offer text")

        assert result["vendor_name"] == "Test Vendor"
        assert result["vat_id"] == "DE987654321"
        assert len(result["order_lines"]) == 1
        assert result["order_lines"][0]["unit_price"] == 150

    @patch('extraction.client')
    def test_extract_offer_data_returns_empty_on_invalid_json(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "not valid json"
        mock_client.chat.completions.create.return_value = mock_response

        from extraction import extract_offer_data
        result = extract_offer_data("Sample text")

        assert result == {}


class TestClassifyCommodityGroup:
    @patch('extraction.client')
    def test_classify_returns_valid_result(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "commodity_group_id": "031",
            "confidence": 0.95,
            "rationale": "Software licenses belong to IT Software category"
        })
        mock_client.chat.completions.create.return_value = mock_response

        from extraction import classify_commodity_group
        result = classify_commodity_group(
            title="Adobe Creative Cloud",
            order_lines=[{"description": "Photoshop License"}],
            vendor_name="Adobe",
            department="Marketing"
        )

        assert result["commodity_group_id"] == "031"
        assert result["confidence"] == 0.95

    @patch('extraction.client')
    def test_classify_fallback_on_invalid_json(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "invalid"
        mock_client.chat.completions.create.return_value = mock_response

        from extraction import classify_commodity_group
        result = classify_commodity_group(
            title="Test",
            order_lines=[{"description": "Item"}]
        )

        assert result["commodity_group_id"] == "009"
        assert result["confidence"] == 0.0
