from fastapi import APIRouter
from app.services.fee_service import get_current_fees, get_fee_history
from app.services.routing_service import calculate_best_route
from app.models.schemas import QuoteRequest

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/fees/current")
def fees():
    return get_current_fees()


@router.get("/fees/history")
def fee_history():
    return get_fee_history()


@router.post("/route/quote")
def quote(req: QuoteRequest):
    return calculate_best_route(req)