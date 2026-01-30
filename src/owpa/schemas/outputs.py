from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TradeOption(BaseModel):
    """
    A proposed give/get bundle with a predicted acceptance likelihood.
    """
    we_offer: str
    we_request: str
    predicted_acceptance: float = Field(..., ge=0.0, le=1.0)
    rationale: List[str] = Field(default_factory=list)  # short bullets, grounded in memory/patterns


class CoachNotes(BaseModel):
    """
    Internal view for procurement specialist.
    """
    summary: List[str] = Field(default_factory=list)
    extracted_facts: List[str] = Field(default_factory=list)
    risks_and_flags: List[str] = Field(default_factory=list)
    recommended_next_move: str
    trade_options: List[TradeOption] = Field(default_factory=list)
    questions_to_ask_supplier: List[str] = Field(default_factory=list)


class EmailDraft(BaseModel):
    """
    External email draft (ready to copy/paste).
    """
    subject: str
    body: str
    tone: str = "professional_firm"
    glossary_terms_used: List[str] = Field(default_factory=list, description="Terms to auto-explain in UI.")
    missing_info_disclaimer: Optional[str] = None  # e.g., "Based on current information..."
