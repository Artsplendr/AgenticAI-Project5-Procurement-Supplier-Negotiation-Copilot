from __future__ import annotations

import re
from datetime import datetime, timedelta

from owpa.agent.state import AgentState
from owpa.agent.utils import llm_json, use_llm
from owpa.schemas.deal_state import Percentage, SupplierAsk


_SYSTEM = """You extract structured facts from supplier emails for WTG+LTSA procurement.
Rules:
- NEVER invent numbers/dates.
- If you extract a number/date, include a short supporting snippet from the email.
Return ONLY JSON.
"""


_SCHEMA = """
{
  "headline_price_change_pct": number|null,
  "requested_trades": [string, ...],
  "deadline_iso": "ISO-8601 datetime string|null",
  "raw_snippets": [string, ...]
}
""".strip()


def _regex_extract_pct(text: str) -> float | None:
    # Finds patterns like "9%" or "+ 9 %"
    m = re.search(r"([+-]?\s*\d{1,2}(\.\d+)?)\s*%", text)
    if not m:
        return None
    s = m.group(1).replace(" ", "")
    try:
        return float(s)
    except Exception:
        return None


def _rule_extract(text: str) -> dict:
    pct = _regex_extract_pct(text)

    trades = []
    t = text.lower()
    if "ld" in t and "cap" in t:
        trades.append("adjust delay LDs cap (LDs = Liquidated Damages)")
    if "payment" in t and "milestone" in t:
        trades.append("change payment milestones / terms")
    if "warranty" in t:
        trades.append("warranty terms adjustment")
    if "index" in t or "indexation" in t:
        trades.append("indexation mechanism (cap/floor)")

    snippets = []
    if pct is not None:
        # best-effort snippet around %
        idx = text.find("%")
        start = max(0, idx - 60)
        end = min(len(text), idx + 60)
        snippets.append(text[start:end].strip())

    # Deadline: very rough fallback (LLM is better). Use "by Friday" heuristic.
    deadline_iso = None
    if "by friday" in t or "sign by friday" in t:
        # assume next Friday 17:00 UTC for demo (explicitly a heuristic)
        # In real use, you'd parse with locale/timezone and supplier context.
        now = datetime.utcnow()
        days_ahead = (4 - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        d = now + timedelta(days=days_ahead)
        deadline_iso = d.replace(hour=17, minute=0, second=0, microsecond=0).isoformat() + "Z"
        snippets.append("by Friday")

    return {
        "headline_price_change_pct": pct,
        "requested_trades": trades,
        "deadline_iso": deadline_iso,
        "raw_snippets": snippets[:5],
    }


def extract_node(state: AgentState) -> AgentState:
    email_text = state.get("email_text", "")

    if use_llm():
        data = llm_json(
            _SYSTEM,
            f"Email:\n{email_text}\n\nExtract key facts. If absent, use null/empty.",
            schema_hint=_SCHEMA,
        )
    else:
        data = _rule_extract(email_text)

    deal = state["deal_state"]
    ask = deal.supplier_ask or SupplierAsk(intent=deal.supplier_ask.intent if deal.supplier_ask else None)  # type: ignore

    pct = data.get("headline_price_change_pct", None)
    if isinstance(pct, (int, float)):
        ask.headline_price_change_pct = Percentage(value=float(pct))

    deadline_iso = data.get("deadline_iso")
    if isinstance(deadline_iso, str) and deadline_iso.strip():
        try:
            # tolerate "Z"
            ask.deadline = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
        except Exception:
            pass

    trades = data.get("requested_trades") or []
    if isinstance(trades, list):
        ask.requested_trades = [str(x) for x in trades if str(x).strip()]

    snippets = data.get("raw_snippets") or []
    if isinstance(snippets, list):
        ask.raw_snippets = [str(x)[:220] for x in snippets if str(x).strip()]

    deal.supplier_ask = ask
    state["deal_state"] = deal
    return state
