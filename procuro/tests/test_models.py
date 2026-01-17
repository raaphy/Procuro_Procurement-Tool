import pytest
from models import ProcurementRequest, OrderLine, StatusHistory, RequestStatus


class TestOrderLine:
    def test_calculated_total_price(self):
        line = OrderLine(
            id=1,
            request_id=1,
            description="Test Item",
            unit_price=100.0,
            quantity=5,
            unit="pieces"
        )
        assert line.calculated_total_price == 500.0

    def test_has_price_mismatch_when_different(self):
        line = OrderLine(
            id=1,
            request_id=1,
            description="Test Item",
            unit_price=100.0,
            quantity=5,
            unit="pieces",
            stated_total_price=600.0
        )
        assert line.has_price_mismatch is True

    def test_has_price_mismatch_when_matching(self):
        line = OrderLine(
            id=1,
            request_id=1,
            description="Test Item",
            unit_price=100.0,
            quantity=5,
            unit="pieces",
            stated_total_price=500.0
        )
        assert line.has_price_mismatch is False

    def test_has_price_mismatch_when_none(self):
        line = OrderLine(
            id=1,
            request_id=1,
            description="Test Item",
            unit_price=100.0,
            quantity=5,
            unit="pieces",
            stated_total_price=None
        )
        assert line.has_price_mismatch is False


class TestProcurementRequest:
    def create_request_with_lines(self, lines_data, stated_total=None):
        request = ProcurementRequest(
            id=1,
            requestor_name="John Doe",
            title="Test Request",
            vendor_name="Test Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="031",
            stated_total_cost=stated_total
        )
        request.order_lines = [
            OrderLine(
                id=i,
                request_id=1,
                description=line["description"],
                unit_price=line["unit_price"],
                quantity=line["quantity"],
                unit="pieces"
            )
            for i, line in enumerate(lines_data)
        ]
        return request

    def test_calculated_total_cost_single_line(self):
        request = self.create_request_with_lines([
            {"description": "Item A", "unit_price": 100.0, "quantity": 2}
        ])
        assert request.calculated_total_cost == 200.0

    def test_calculated_total_cost_multiple_lines(self):
        request = self.create_request_with_lines([
            {"description": "Item A", "unit_price": 100.0, "quantity": 2},
            {"description": "Item B", "unit_price": 50.0, "quantity": 3}
        ])
        assert request.calculated_total_cost == 350.0

    def test_has_total_mismatch_when_different(self):
        request = self.create_request_with_lines(
            [{"description": "Item A", "unit_price": 100.0, "quantity": 2}],
            stated_total=300.0
        )
        assert request.has_total_mismatch is True

    def test_has_total_mismatch_when_matching(self):
        request = self.create_request_with_lines(
            [{"description": "Item A", "unit_price": 100.0, "quantity": 2}],
            stated_total=200.0
        )
        assert request.has_total_mismatch is False

    def test_has_total_mismatch_when_none(self):
        request = self.create_request_with_lines(
            [{"description": "Item A", "unit_price": 100.0, "quantity": 2}],
            stated_total=None
        )
        assert request.has_total_mismatch is False


class TestRequestStatus:
    def test_status_values(self):
        assert RequestStatus.OPEN.value == "Open"
        assert RequestStatus.IN_PROGRESS.value == "In Progress"
        assert RequestStatus.CLOSED.value == "Closed"
