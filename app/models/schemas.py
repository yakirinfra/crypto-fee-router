from pydantic import BaseModel


class QuoteRequest(BaseModel):
    token: str
    amount: float
    source_chain: str
    destination_chain: str
    cost_weight: float = 0.4
    speed_weight: float = 0.2
    reliability_weight: float = 0.2
    risk_weight: float = 0.2