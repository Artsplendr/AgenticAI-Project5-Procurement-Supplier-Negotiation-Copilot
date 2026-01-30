from __future__ import annotations

from owpa.agent.state import AgentState
from owpa.glossary import DEFAULT_GLOSSARY
from owpa.schemas.outputs import EmailDraft, TradeOption


def draft_email_node(state: AgentState) -> AgentState:
    deal = state["deal_state"]
    ask = deal.supplier_ask

    trade_options = []
    raw = deal.metadata.get("trade_options", [])
    if isinstance(raw, list):
        for item in raw:
            try:
                trade_options.append(TradeOption.model_validate(item))
            except Exception:
                pass

    # Pick best trade option for the draft (top-ranked)
    chosen = trade_options[0] if trade_options else None

    subject = f"Re: WTG + LTSA commercial alignment and next steps"

    # Keep it procurement-safe: no internal targets, no invented numbers
    lines = []
    lines.append(f"Dear {deal.supplier_name} team,")
    lines.append("")
    lines.append("Thank you for your message. We have reviewed your latest note and would like to align on a path that preserves schedule certainty and a bankable risk profile.")
    lines.append("")

    if ask and ask.headline_price_change_pct:
        lines.append(
            f"You referenced a requested adjustment of {ask.headline_price_change_pct.value:.1f}%. "
            "To progress efficiently, please share a brief breakdown of the drivers and whether a capped indexation approach could cover part of the exposure."
        )
    else:
        lines.append("To progress efficiently, please share a brief breakdown of the commercial drivers and whether a capped indexation approach could cover part of the exposure.")

    lines.append("")

    if chosen:
        lines.append("From our side, we suggest the following trade package to close the gap:")
        lines.append(f"- We can offer: {chosen.we_offer}")
        lines.append(f"- In return, we request: {chosen.we_request}")
        lines.append("")
        lines.append("If this direction works, we can turn it quickly into an updated commercial note and an agreed next step on the contract schedule.")
    else:
        lines.append("From our side, we suggest aligning via a balanced give/get package (commercial + risk allocation) and then confirming the next step on the contract schedule.")

    lines.append("")
    lines.append("Best regards,")
    lines.append("Procurement Team")

    # glossary term detection (very lightweight)
    glossary_used = []
    body = "\n".join(lines)
    for term in ["WTG", "LTSA", "LDs", "Indexation", "Availability guarantee"]:
        if term in body:
            glossary_used.append(term)

    draft = EmailDraft(
        subject=subject,
        body=body,
        tone="professional_firm",
        glossary_terms_used=glossary_used,
        missing_info_disclaimer="Draft is based on the current email context; please verify numbers/dates against the source message before sending.",
    )

    state["email_draft"] = draft
    return state
