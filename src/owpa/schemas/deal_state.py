from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PackageType(str, Enum):
    WTG_LTSA = "WTG+LTSA"  # Wind Turbine Generator supply + Long-Term Service Agreement


class IntentType(str, Enum):
    PRICE_INCREASE_REQUEST = "price_increase_request"
    COUNTER_TO_OUR_OFFER = "counter_to_our_offer"
    SLOT_PRESSURE_DEADLINE = "slot_pressure_deadline"  # manufacturing slot / capacity pressure
    CONTRACT_REDLINE = "contract_redline"              # liability/warranty/terms redlines
    INFO_REQUEST = "info_request"
    OTHER = "other"


class Money(BaseModel):
    amount: float = Field(..., description="Numeric amount. Must be grounded in input when extracted.")
    currency: str = Field(..., description="ISO-like currency code, e.g. EUR, USD, GBP.")


class Percentage(BaseModel):
    value: float = Field(..., description="Percent value, e.g. 9.0 means 9%.")


class DateWindow(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None
    notes: Optional[str] = None


class SupplierAsk(BaseModel):
    """What the supplier is currently asking for (from latest email/round)."""
    intent: IntentType
    headline_price_change_pct: Optional[Percentage] = None  # e.g., +9%
    headline_price_change_amount: Optional[Money] = None    # e.g., +€12M (if stated)
    reason: Optional[str] = None                            # e.g., "input costs", "capacity constraints"
    deadline: Optional[datetime] = None                     # e.g., "sign by Friday 17:00"
    requested_trades: List[str] = Field(default_factory=list)  # e.g., "reduce LD cap", "change payment milestone"
    raw_snippets: List[str] = Field(
        default_factory=list,
        description="Short verbatim snippets (<=25 words each) from the email to support extracted facts."
    )


class OurPosition(BaseModel):
    """Optional in v1; include if the user provides it."""
    target_price_change_pct: Optional[Percentage] = None
    max_price_change_pct: Optional[Percentage] = None  # walk-away on uplift (if using uplift framing)
    preferred_trades: List[str] = Field(default_factory=list)  # e.g., "indexation cap", "extend warranty"
    notes: Optional[str] = None


class OpenIssue(BaseModel):
    topic: str  # e.g., "Indexation clause", "Availability definition", "LD cap"
    status: Literal["open", "pending_supplier", "pending_internal", "agreed", "rejected"] = "open"
    detail: Optional[str] = None


class ConcessionEntry(BaseModel):
    """
    Concession ledger entry: track give/get over time.
    'Give' should always be paired with a 'Get' (negotiation discipline).
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    we_gave: str
    we_got: str
    value_note: Optional[str] = None  # lightweight value estimate rationale
    approval_required: bool = False
    evidence: List[str] = Field(default_factory=list, description="Short supporting snippets or refs")


class DealState(BaseModel):
    """
    State for one negotiation thread (WTG+LTSA package with one supplier).
    Kept intentionally small for MVP.
    """
    deal_id: str = Field(..., description="Stable identifier for this negotiation thread.")
    package: PackageType = PackageType.WTG_LTSA

    supplier_name: str
    round_number: int = 0

    # Latest incoming email/context
    last_supplier_email_subject: Optional[str] = None
    last_supplier_email_received_at: Optional[datetime] = None
    supplier_ask: Optional[SupplierAsk] = None

    # Optional (provided by buyer / internal)
    our_position: Optional[OurPosition] = None

    # Tracker
    open_issues: List[OpenIssue] = Field(default_factory=list)
    concessions: List[ConcessionEntry] = Field(default_factory=list)

    # Key schedule anchors (optional in v1; useful later)
    manufacturing_slot_window: Optional[DateWindow] = None
    delivery_window: Optional[DateWindow] = None

    # Storage / audit
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
