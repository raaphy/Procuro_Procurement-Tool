from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
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
    status = Column(String, default=RequestStatus.OPEN.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_lines = relationship("OrderLine", back_populates="request", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="request", cascade="all, delete-orphan")

    @property
    def total_cost(self) -> float:
        return sum(line.unit_price * line.quantity for line in self.order_lines)


class OrderLine(Base):
    __tablename__ = "order_lines"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("procurement_requests.id"), nullable=False)
    description = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String, nullable=False)

    request = relationship("ProcurementRequest", back_populates="order_lines")

    @property
    def total_price(self) -> float:
        return self.unit_price * self.quantity


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("procurement_requests.id"), nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String, default="system")

    request = relationship("ProcurementRequest", back_populates="status_history")
