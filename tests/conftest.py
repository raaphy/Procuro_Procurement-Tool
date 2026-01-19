import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from database.database import get_db
from database.models import Base


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_request_data():
    return {
        "requestor_name": "Max Mustermann",
        "title": "Office Supplies Order",
        "vendor_name": "Bürobedarf GmbH",
        "vat_id": "DE123456789",
        "department": "IT",
        "commodity_group_id": "031",
        "currency": "EUR",
        "stated_total_cost": 1000.0,
        "order_lines": [
            {
                "description": "Laptop",
                "unit_price": 500.0,
                "quantity": 2,
                "unit": "pieces",
                "stated_total_price": 1000.0,
            }
        ],
    }


@pytest.fixture
def sample_request_data_with_mismatch():
    return {
        "requestor_name": "Test User",
        "title": "Test Order",
        "vendor_name": "Test Vendor",
        "vat_id": "DE987654321",
        "department": "HR",
        "commodity_group_id": "001",
        "currency": "EUR",
        "stated_total_cost": 600.0,
        "order_lines": [
            {
                "description": "Item 1",
                "unit_price": 100.0,
                "quantity": 2,
                "unit": "pcs",
                "stated_total_price": 250.0,
            },
            {
                "description": "Item 2",
                "unit_price": 150.0,
                "quantity": 2,
                "unit": "pcs",
                "stated_total_price": 350.0,
            },
        ],
    }
