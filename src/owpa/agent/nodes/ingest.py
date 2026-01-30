from __future__ import annotations

from datetime import datetime

from owpa.agent.state import AgentState


def ingest_node(state: AgentState) -> AgentState:
    deal = state["deal_state"]

    email_text = (state.get("email_text") or "").strip()
    subject = (state.get("supplier_email_subject") or "").strip()

    deal.last_supplier_email_subject = subject or deal.last_supplier_email_subject
    deal.last_supplier_email_received_at = datetime.utcnow()
    deal.metadata["last_email_text"] = email_text  # kept internal; do not send externally
    deal.last_updated_at = datetime.utcnow()

    state["deal_state"] = deal
    return state
