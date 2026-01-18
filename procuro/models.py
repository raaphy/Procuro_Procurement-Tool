from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, LargeBinary
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class RequestStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    CLOSED = "Closed"


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(Integer, primary_key=True, index=True)
    requestor_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    vendor_name = Column(String, nullable=False)
    vat_id = Column(String, nullable=False)
    department = Column(String, nullable=False)
    commodity_group_id = Column(String, nullable=False)
    currency = Column(String, default="EUR")
    stated_total_cost = Column(Float, nullable=True)  # Total from the offer document
    status = Column(String, default=RequestStatus.OPEN.value)
    pdf_data = Column(LargeBinary, nullable=True)  # Stored PDF file
    pdf_filename = Column(String, nullable=True)  # Original filename
    created_at = Column(DateTime, default=datetime.utcnow) # TODO deprecated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_lines = relationship("OrderLine", back_populates="request", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="request", cascade="all, delete-orphan")

    @property
    def calculated_total_cost(self) -> float:
        return sum(line.unit_price * line.quantity for line in self.order_lines)
    
    @property
    def has_total_mismatch(self) -> bool:
        if self.stated_total_cost is None:
            return False
        return abs(self.stated_total_cost - self.calculated_total_cost) > 0.01


class OrderLine(Base):
    __tablename__ = "order_lines"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("procurement_requests.id"), nullable=False)
    description = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)

    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    stated_total_price = Column(Float, nullable=True)  # Total from the offer document

    request = relationship("ProcurementRequest", back_populates="order_lines")

    @property
    def calculated_total_price(self) -> float:
        return self.unit_price * self.quantity
    
    @property
    def has_price_mismatch(self) -> bool:
        if self.stated_total_price is None:
            return False
        return abs(self.stated_total_price - self.calculated_total_price) > 0.01


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("procurement_requests.id"), nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String, default="system")

    request = relationship("ProcurementRequest", back_populates="status_history")
