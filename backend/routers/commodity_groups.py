from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.extraction import classify_commodity_group
from backend.schemas import CommodityGroupResponse, ClassificationResponse
from database.commodity_groups import COMMODITY_GROUPS

router = APIRouter(prefix="/api/commodity-groups", tags=["commodity-groups"])


class SimpleClassificationRequest(BaseModel):
    description: str


@router.get("", response_model=list[CommodityGroupResponse])
def list_commodity_groups():
    return [
        CommodityGroupResponse(id=g["id"], category=g["category"], name=g["name"])
        for g in COMMODITY_GROUPS
    ]


@router.post("/classify", response_model=ClassificationResponse)
def classify_commodity(data: SimpleClassificationRequest):
    try:
        result = classify_commodity_group(
            title=data.description,
            order_lines=[],
            vendor_name="",
            department="",
        )
        return ClassificationResponse(
            commodity_group_id=result.get("commodity_group_id", "009"),
            confidence=result.get("confidence", 0.0),
            rationale=result.get("rationale", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
