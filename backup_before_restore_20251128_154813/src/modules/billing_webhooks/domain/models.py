from typing import Dict

from pydantic import BaseModel


class BillingEvent(BaseModel):
    """Billing event model"""

    type: str
    data: Dict
