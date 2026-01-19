import pytest


class TestCreateRequest:
    def test_create_request_success(self, client, sample_request_data):
        response = client.post("/api/requests", json=sample_request_data)
        assert response.status_code == 201
        data = response.json()
        
        assert data["requestor_name"] == sample_request_data["requestor_name"]
        assert data["title"] == sample_request_data["title"]
        assert data["vendor_name"] == sample_request_data["vendor_name"]
        assert data["status"] == "Open"
        
        assert len(data["order_lines"]) == 1
        assert data["order_lines"][0]["description"] == "Laptop"
        assert data["order_lines"][0]["unit_price"] == 500.0
        assert data["order_lines"][0]["quantity"] == 2
        
        assert len(data["status_history"]) == 1
        assert data["status_history"][0]["from_status"] is None
        assert data["status_history"][0]["to_status"] == "Open"


class TestGetRequest:
    def test_get_request_by_id(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        request_id = create_response.json()["id"]

        response = client.get(f"/api/requests/{request_id}")
        assert response.status_code == 200
        assert response.json()["id"] == request_id

    def test_get_request_not_found(self, client):
        response = client.get("/api/requests/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Request not found"


class TestListRequests:
    def test_list_requests_empty(self, client):
        response = client.get("/api/requests")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_requests(self, client, sample_request_data):
        client.post("/api/requests", json=sample_request_data)
        client.post("/api/requests", json=sample_request_data)

        response = client.get("/api/requests")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_requests_filter_by_status(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        request_id = create_response.json()["id"]
        
        client.patch(
            f"/api/requests/{request_id}/status",
            json={"status": "In Progress", "changed_by": "test"},
        )

        open_response = client.get("/api/requests?status=Open")
        assert len(open_response.json()) == 0

        in_progress_response = client.get("/api/requests?status=In Progress")
        assert len(in_progress_response.json()) == 1

    def test_list_requests_search(self, client, sample_request_data):
        client.post("/api/requests", json=sample_request_data)

        response = client.get("/api/requests?search=Office")
        assert len(response.json()) == 1

        response = client.get("/api/requests?search=Bürobedarf")
        assert len(response.json()) == 1

        response = client.get("/api/requests?search=NotExisting")
        assert len(response.json()) == 0


class TestUpdateRequest:
    def test_update_request(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        request_id = create_response.json()["id"]

        update_data = {"title": "Updated Title", "vendor_name": "New Vendor"}
        response = client.put(f"/api/requests/{request_id}", json=update_data)

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
        assert response.json()["vendor_name"] == "New Vendor"

    def test_update_request_order_lines(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        request_id = create_response.json()["id"]

        update_data = {
            "order_lines": [
                {"description": "New Item", "unit_price": 100.0, "quantity": 5, "unit": "pcs", "stated_total_price": 500.0}
            ]
        }
        response = client.put(f"/api/requests/{request_id}", json=update_data)

        assert response.status_code == 200
        assert len(response.json()["order_lines"]) == 1
        assert response.json()["order_lines"][0]["description"] == "New Item"

    def test_update_request_not_found(self, client):
        response = client.put("/api/requests/99999", json={"title": "Test"})
        assert response.status_code == 404


class TestStatusUpdate:
    def test_update_status(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        request_id = create_response.json()["id"]

        response = client.patch(
            f"/api/requests/{request_id}/status",
            json={"status": "In Progress", "changed_by": "admin"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "In Progress"

    def test_status_history_created(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        request_id = create_response.json()["id"]

        client.patch(
            f"/api/requests/{request_id}/status",
            json={"status": "In Progress", "changed_by": "admin"},
        )
        client.patch(
            f"/api/requests/{request_id}/status",
            json={"status": "Closed", "changed_by": "admin"},
        )

        response = client.get(f"/api/requests/{request_id}")
        history = response.json()["status_history"]

        assert len(history) == 3
        assert history[0]["to_status"] == "Open"
        assert history[1]["from_status"] == "Open"
        assert history[1]["to_status"] == "In Progress"
        assert history[2]["from_status"] == "In Progress"
        assert history[2]["to_status"] == "Closed"

    def test_update_status_not_found(self, client):
        response = client.patch(
            "/api/requests/99999/status",
            json={"status": "Closed", "changed_by": "admin"},
        )
        assert response.status_code == 404


class TestDeleteRequest:
    def test_delete_request(self, client, sample_request_data):
        create_response = client.post("/api/requests", json=sample_request_data)
        request_id = create_response.json()["id"]

        response = client.delete(f"/api/requests/{request_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/requests/{request_id}")
        assert get_response.status_code == 404

    def test_delete_request_not_found(self, client):
        response = client.delete("/api/requests/99999")
        assert response.status_code == 404
