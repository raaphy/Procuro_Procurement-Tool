import pytest
from pathlib import Path


class TestFullWorkflow:
    def test_create_update_status_delete(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        assert create_response.status_code == 201
        request_id = create_response.json()["id"]
        assert create_response.json()["status"] == "Open"

        update_response = client.put(
            f"/api/requests/{request_id}",
            json={"title": "Updated Order", "vendor_name": "New Vendor GmbH"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Order"

        status_response = client.patch(
            f"/api/requests/{request_id}/status",
            json={"status": "In Progress", "changed_by": "manager"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "In Progress"

        status_response = client.patch(
            f"/api/requests/{request_id}/status",
            json={"status": "Closed", "changed_by": "manager"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "Closed"

        get_response = client.get(f"/api/requests/{request_id}")
        history = get_response.json()["status_history"]
        assert len(history) == 3

        delete_response = client.delete(f"/api/requests/{request_id}")
        assert delete_response.status_code == 204

        get_deleted = client.get(f"/api/requests/{request_id}")
        assert get_deleted.status_code == 404


class TestCalculatedFields:
    def test_calculated_total_cost_matches(self, client, sample_request_data):
        response = client.post("/api/requests", json=sample_request_data)
        data = response.json()

        assert data["calculated_total_cost"] == 1000.0
        assert data["has_total_mismatch"] is False

    def test_total_mismatch_detected(self, client, sample_request_data_with_mismatch):
        response = client.post("/api/requests", json=sample_request_data_with_mismatch)
        data = response.json()

        assert data["calculated_total_cost"] == 500.0
        assert data["stated_total_cost"] == 600.0
        assert data["has_total_mismatch"] is True

    def test_order_line_mismatch_detected(self, client, sample_request_data_with_mismatch):
        response = client.post("/api/requests", json=sample_request_data_with_mismatch)
        data = response.json()

        mismatches = [line for line in data["order_lines"] if line["has_price_mismatch"]]
        assert len(mismatches) == 2


class TestPDFUploadAPI:
    def test_upload_pdf_endpoint(self, client):
        pdf_path = Path(__file__).parent / "example_offer.pdf"
        
        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/extraction/pdf",
                files={"file": ("example_offer.pdf", f, "application/pdf")},
            )
        
        assert response.status_code in [200]

    def test_upload_non_pdf_rejected(self, client):
        response = client.post(
            "/api/extraction/pdf",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_empty_file_rejected(self, client):
        response = client.post(
            "/api/extraction/pdf",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        
        assert response.status_code == 400


class TestClassificationAPI:
    def test_classification_endpoint(self, client):
        response = client.post(
            "/api/extraction/classify",
            json={
                "title": "Software Licenses",
                "order_lines": [{"description": "Microsoft Office 365"}],
                "vendor_name": "Microsoft",
                "department": "IT",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["commodity_group_id"] == "031"  # Software
