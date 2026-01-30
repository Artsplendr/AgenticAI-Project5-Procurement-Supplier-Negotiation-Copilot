from __future__ import annotations

import re

from owpa.agent.state import AgentState
from owpa.agent.utils import llm_json, use_llm
from owpa.schemas.deal_state import IntentType, SupplierAsk


_SYSTEM = """You classify supplier procurement emails for offshore wind WTG+LTSA.
Return only JSON. Do not invent facts.
"""


_SCHEMA = """
{
  "intent": "price_increase_request | counter_to_our_offer | slot_pressure_deadline | contract_redline | info_request | other",
  "reason": "string|null"
}
""".strip()


def _rule_classify(text: str) -> dict:
    t = text.lower()
    if any(k in t for k in ["increase", "uplift", "adjustment", "%", "escalation", "inflation"]):
        return {"intent": "price_increase_request", "reason": "possible cost escalation / uplift request"}
    if any(k in t for k in ["sign by", "deadline", "this week", "by friday", "slot", "capacity"]):
        return {"intent": "slot_pressure_deadline", "reason": "possible manufacturing slot / deadline pressure"}
    if any(k in t for k in ["redline", "liability", "warranty", "consequential", "indemnity"]):
        return {"intent": "contract_redline", "reason": "contract terms / risk allocation"}
    if "please confirm" in t or "could you provide" in t or "we need" in t:
        return {"intent": "info_request", "reason": "requesting information"}
    return {"intent": "other", "reason": None}


def classify_node(state: AgentState) -> AgentState:
    email_text = state.get("email_text", "")

    if use_llm():
        data = llm_json(
            _SYSTEM,
            f"Email:\n{email_text}\n\nClassify the intent.",
            schema_hint=_SCHEMA,
        )
    else:
        data = _rule_classify(email_text)

    intent_str = (data.get("intent") or "other").strip()
    reason = data.get("reason")

    try:
        intent = IntentType(intent_str)
    except Exception:
        intent = IntentType.OTHER

    deal = state["deal_state"]
    ask = deal.supplier_ask or SupplierAsk(intent=intent)
    ask.intent = intent
    ask.reason = reason or ask.reason

    # keep snippets empty here; extraction node will add evidence
    deal.supplier_ask = ask
    state["deal_state"] = deal
    return state
