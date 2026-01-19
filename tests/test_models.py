import pytest
from database.models import ProcurementRequest, OrderLine, StatusHistory, RequestStatus


class TestProcurementRequestModel:
    def test_total_cost_with_mismatch(self, test_db):
        request = ProcurementRequest(
            requestor_name="Test",
            title="Test Order",
            vendor_name="Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="001",
            stated_total_cost=500.0,
        )
        line1 = OrderLine(description="Item 1", unit_price=100.0, quantity=2, unit="pcs")
        line2 = OrderLine(description="Item 2", unit_price=50.0, quantity=3, unit="pcs")
        request.order_lines.extend([line1, line2])
        
        test_db.add(request)
        test_db.commit()
        
        assert request.calculated_total_cost == 350.0
        assert request.has_total_mismatch is True

    def test_total_cost_without_mismatch(self, test_db):
        request = ProcurementRequest(
            requestor_name="Test",
            title="Test Order",
            vendor_name="Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="001",
            stated_total_cost=200.0,
        )
        line = OrderLine(description="Item", unit_price=100.0, quantity=2, unit="pcs")
        request.order_lines.append(line)
        
        test_db.add(request)
        test_db.commit()
        
        assert request.calculated_total_cost == 200.0
        assert request.has_total_mismatch is False

    def test_total_cost_empty_lines(self, test_db):
        request = ProcurementRequest(
            requestor_name="Test",
            title="Test Order",
            vendor_name="Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="001",
            stated_total_cost=None,
        )
        test_db.add(request)
        test_db.commit()
        
        assert request.calculated_total_cost == 0.0
        assert request.has_total_mismatch is False


class TestOrderLineModel:
    def test_line_price_with_mismatch(self, test_db):
        request = ProcurementRequest(
            requestor_name="Test",
            title="Test",
            vendor_name="Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="001",
        )
        line = OrderLine(
            description="Item",
            unit_price=100.0,
            quantity=2,
            unit="pcs",
            stated_total_price=250.0,
        )
        request.order_lines.append(line)
        
        test_db.add(request)
        test_db.commit()
        
        assert line.calculated_total_price == 200.0
        assert line.has_price_mismatch is True

    def test_line_price_without_mismatch(self, test_db):
        request = ProcurementRequest(
            requestor_name="Test",
            title="Test",
            vendor_name="Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="001",
        )
        line = OrderLine(
            description="Item",
            unit_price=75.50,
            quantity=4,
            unit="pcs",
            stated_total_price=302.0,
        )
        request.order_lines.append(line)
        
        test_db.add(request)
        test_db.commit()
        
        assert line.calculated_total_price == 302.0
        assert line.has_price_mismatch is False

    def test_line_price_none_stated(self, test_db):
        request = ProcurementRequest(
            requestor_name="Test",
            title="Test",
            vendor_name="Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="001",
        )
        line = OrderLine(
            description="Item",
            unit_price=100.0,
            quantity=2,
            unit="pcs",
            stated_total_price=None,
        )
        request.order_lines.append(line)
        
        test_db.add(request)
        test_db.commit()
        
        assert line.calculated_total_price == 200.0
        assert line.has_price_mismatch is False


class TestStatusHistoryModel:
    def test_status_history_creation(self, test_db):
        request = ProcurementRequest(
            requestor_name="Test",
            title="Test",
            vendor_name="Vendor",
            vat_id="DE123456789",
            department="IT",
            commodity_group_id="001",
        )
        history = StatusHistory(
            from_status=None,
            to_status=RequestStatus.OPEN.value,
            changed_by="system",
        )
        request.status_history.append(history)
        
        test_db.add(request)
        test_db.commit()
        
        assert history.id is not None
        assert history.to_status == "Open"
        assert history.changed_at is not None


class TestRequestStatusEnum:
    def test_status_values(self):
        assert RequestStatus.OPEN.value == "Open"
        assert RequestStatus.IN_PROGRESS.value == "In Progress"
        assert RequestStatus.CLOSED.value == "Closed"
