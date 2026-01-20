import os
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database.database import get_db, UPLOAD_DIR
from backend.schemas import (
    ProcurementRequestCreate,
    ProcurementRequestUpdate,
    ProcurementRequestResponse,
    ProcurementRequestListResponse,
    StatusUpdateRequest,
)
from database.models import ProcurementRequest, OrderLine, StatusHistory, RequestStatus

router = APIRouter(prefix="/api/requests", tags=["requests"])


@router.get("", response_model=list[ProcurementRequestListResponse])
def list_requests(
    status: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ProcurementRequest)

    if status:
        query = query.filter(ProcurementRequest.status == status)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (ProcurementRequest.title.ilike(search_pattern))
            | (ProcurementRequest.vendor_name.ilike(search_pattern))
            | (ProcurementRequest.requestor_name.ilike(search_pattern))
        )

    requests = query.order_by(ProcurementRequest.created_at.desc()).all()
    return requests


@router.get("/{request_id}", response_model=ProcurementRequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@router.post("", response_model=ProcurementRequestResponse, status_code=201)
def create_request(data: ProcurementRequestCreate, db: Session = Depends(get_db)):
    request = ProcurementRequest(
        requestor_name=data.requestor_name,
        title=data.title,
        vendor_name=data.vendor_name,
        vat_id=data.vat_id,
        department=data.department,
        commodity_group_id=data.commodity_group_id,
        currency=data.currency,
        stated_total_cost=data.stated_total_cost,
        status=RequestStatus.OPEN.value,
    )

    for line_data in data.order_lines:
        line = OrderLine(
            description=line_data.description,
            unit_price=line_data.unit_price,
            quantity=line_data.quantity,
            unit=line_data.unit,
            stated_total_price=line_data.stated_total_price,
        )
        request.order_lines.append(line)

    history = StatusHistory(
        from_status=None,
        to_status=RequestStatus.OPEN.value,
        changed_by="system",
    )
    request.status_history.append(history)

    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.put("/{request_id}", response_model=ProcurementRequestResponse)
def update_request(request_id: int, data: ProcurementRequestUpdate, db: Session = Depends(get_db)):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if data.requestor_name is not None:
        request.requestor_name = data.requestor_name
    if data.title is not None:
        request.title = data.title
    if data.vendor_name is not None:
        request.vendor_name = data.vendor_name
    if data.vat_id is not None:
        request.vat_id = data.vat_id
    if data.department is not None:
        request.department = data.department
    if data.commodity_group_id is not None:
        request.commodity_group_id = data.commodity_group_id
    if data.currency is not None:
        request.currency = data.currency
    if data.stated_total_cost is not None:
        request.stated_total_cost = data.stated_total_cost

    if data.order_lines is not None:
        for line in request.order_lines:
            db.delete(line)

        for line_data in data.order_lines:
            line = OrderLine(
                description=line_data.description,
                unit_price=line_data.unit_price,
                quantity=line_data.quantity,
                unit=line_data.unit,
                stated_total_price=line_data.stated_total_price,
            )
            request.order_lines.append(line)

    db.commit()
    db.refresh(request)
    return request


@router.patch("/{request_id}/status", response_model=ProcurementRequestResponse)
def update_status(request_id: int, data: StatusUpdateRequest, db: Session = Depends(get_db)):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    old_status = request.status
    new_status = data.status.value

    if old_status != new_status:
        request.status = new_status

        history = StatusHistory(
            from_status=old_status,
            to_status=new_status,
            changed_by=data.changed_by,
        )
        request.status_history.append(history)

        db.commit()
        db.refresh(request)

    return request


@router.delete("/{request_id}", status_code=204)
def delete_request(request_id: int, db: Session = Depends(get_db)):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.pdf_filename:
        filepath = UPLOAD_DIR / request.pdf_filename
        if filepath.exists():
            filepath.unlink()

    db.delete(request)
    db.commit()
    return None

@router.post("/{request_id}/pdf", status_code=200)
async def upload_pdf(request_id:int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (UPLOAD_DIR / f"{request_id}.pdf").write_bytes(file_bytes)
        request.pdf_filename = f"{request_id}.pdf"
        db.commit()
        return {"message": "PDF uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")


@router.get("/{request_id}/pdf")
def get_pdf(request_id: int, db: Session = Depends(get_db)):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request or not request.pdf_filename:
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(UPLOAD_DIR / request.pdf_filename, media_type="application/pdf")


@router.delete("/{request_id}/pdf", status_code=204)
def delete_pdf(request_id: int, db: Session = Depends(get_db)):
    request = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.pdf_filename:
        filepath = UPLOAD_DIR / request.pdf_filename
        if filepath.exists():
            filepath.unlink()
        request.pdf_filename = None
        db.commit()
    return None
        