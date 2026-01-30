from __future__ import annotations

from typing import Optional, TypedDict

from owpa.schemas.deal_state import DealState
from owpa.schemas.outputs import CoachNotes, EmailDraft
from owpa.schemas.supplier_memory import SupplierMemory


class AgentState(TypedDict, total=False):
    email_text: str
    supplier_email_subject: str

    deal_state: DealState
    supplier_memory: SupplierMemory
    playbook: dict

    coach_notes: CoachNotes
    email_draft: EmailDraft