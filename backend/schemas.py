from datetime import datetime
from pydantic import BaseModel
from database.models import RequestStatus


class OrderLineCreate(BaseModel):
    description: str
    unit_price: float
    quantity: float
    unit: str
    stated_total_price: float | None = None


class OrderLineResponse(BaseModel):
    id: int
    description: str
    unit_price: float
    quantity: float
    unit: str
    stated_total_price: float | None
    calculated_total_price: float
    has_price_mismatch: bool

    model_config = {"from_attributes": True}


class StatusHistoryResponse(BaseModel):
    id: int
    from_status: str | None
    to_status: str
    changed_at: datetime
    changed_by: str

    model_config = {"from_attributes": True}


class ProcurementRequestCreate(BaseModel):
    requestor_name: str
    title: str
    vendor_name: str
    vat_id: str
    department: str
    commodity_group_id: str
    currency: str = "EUR"
    stated_total_cost: float | None = None
    order_lines: list[OrderLineCreate] = []


class ProcurementRequestUpdate(BaseModel):
    requestor_name: str | None = None
    title: str | None = None
    vendor_name: str | None = None
    vat_id: str | None = None
    department: str | None = None
    commodity_group_id: str | None = None
    currency: str | None = None
    stated_total_cost: float | None = None
    order_lines: list[OrderLineCreate] | None = None


class ProcurementRequestResponse(BaseModel):
    id: int
    requestor_name: str
    title: str
    vendor_name: str
    vat_id: str
    department: str
    commodity_group_id: str
    currency: str
    stated_total_cost: float | None
    status: str
    pdf_filename: str | None
    created_at: datetime
    updated_at: datetime
    order_lines: list[OrderLineResponse]
    status_history: list[StatusHistoryResponse]
    calculated_total_cost: float
    has_total_mismatch: bool

    model_config = {"from_attributes": True}


class ProcurementRequestListResponse(BaseModel):
    id: int
    requestor_name: str
    title: str
    vendor_name: str
    vat_id: str
    department: str
    commodity_group_id: str
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    calculated_total_cost: float
    stated_total_cost: float | None
    has_total_mismatch: bool
    pdf_filename: str | None
    order_lines: list[OrderLineResponse]
    status_history: list[StatusHistoryResponse]

    model_config = {"from_attributes": True}


class StatusUpdateRequest(BaseModel):
    status: RequestStatus
    changed_by: str = "system"


class ExtractionResponse(BaseModel):
    vendor_name: str | None = None
    vat_id: str | None = None
    department: str | None = None
    requestor_name: str | None = None
    title: str | None = None
    currency: str | None = None
    order_lines: list[dict] = []
    stated_total_cost: float | None = None


class ClassificationRequest(BaseModel):
    title: str
    order_lines: list[dict]
    vendor_name: str = ""
    department: str = ""


class ClassificationResponse(BaseModel):
    commodity_group_id: str
    confidence: float
    rationale: str


class CommodityGroupResponse(BaseModel):
    id: str
    category: str
    name: str
