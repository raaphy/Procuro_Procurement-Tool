from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.schemas import ExtractionResponse, ClassificationRequest, ClassificationResponse
from backend.extraction import extract_offer_data_from_pdf, classify_commodity_group

router = APIRouter(prefix="/api/extraction", tags=["extraction"])


@router.post("/pdf", response_model=ExtractionResponse)
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = extract_offer_data_from_pdf(file_bytes)
        return ExtractionResponse(
            vendor_name=result.get("vendor_name"),
            vat_id=result.get("vat_id"),
            department=result.get("department"),
            requestor_name=result.get("requestor_name"),
            title=result.get("title"),
            currency=result.get("currency"),
            order_lines=result.get("order_lines", []),
            stated_total_cost=result.get("stated_total_cost"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/classify-commodity", response_model=ClassificationResponse)
def classify_commodity(data: ClassificationRequest):
    try:
        result = classify_commodity_group(
            title=data.title,
            order_lines=data.order_lines,
            vendor_name=data.vendor_name,
            department=data.department,
        )
        return ClassificationResponse(
            commodity_group_id=result.get("commodity_group_id", "009"),
            confidence=result.get("confidence", 0.0),
            rationale=result.get("rationale", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
