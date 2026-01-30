from __future__ import annotations

from datetime import date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MovementPreferences(BaseModel):
    """
    0..1 weights for how likely the supplier is to move on each lever.
    Higher means: easier to win concessions there.
    """
    price: float = 0.3
    payment_terms: float = 0.7
    warranty_liability: float = 0.5
    schedule_slots: float = 0.4
    service_scope: float = 0.6


class NegotiationEpisode(BaseModel):
    """
    One historical negotiation outcome (synthetic for MVP).
    Keep it structured so we can match patterns later.
    """
    context: str = Field(..., description="Short context like 'WTG+LTSA renewal, North Sea project'.")
    supplier_opening_ask_pct: Optional[float] = None     # e.g., 9.0
    settled_pct: Optional[float] = None                 # e.g., 3.0
    primary_trade_used: Optional[str] = None            # e.g., 'earlier milestone payment'
    outcome: Literal["won", "mixed", "lost"] = "mixed"   # buyer-centric, simple
    notes: Optional[str] = None
    year: Optional[int] = None


class SupplierMemory(BaseModel):
    supplier_id: str
    name: str

    style: Literal["collaborative", "aggressive", "deadline_driven", "formal", "variable"] = "variable"
    typical_tactics: List[str] = Field(default_factory=list)  # e.g., "capacity scarcity", "anchor high"

    movement_preferences: MovementPreferences = Field(default_factory=MovementPreferences)

    # Simple “what worked” memory
    successful_trades: List[str] = Field(default_factory=list)
    sensitive_points: List[str] = Field(default_factory=list)  # e.g., "unlimited liability rejected"

    # Episodes = the source for MVP prediction
    episodes: List[NegotiationEpisode] = Field(default_factory=list)

    last_updated: Optional[date] = None
