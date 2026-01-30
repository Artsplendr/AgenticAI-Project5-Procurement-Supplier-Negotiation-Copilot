from __future__ import annotations

from owpa.agent.state import AgentState
from owpa.schemas.outputs import CoachNotes, TradeOption


def coach_node(state: AgentState) -> AgentState:
    deal = state["deal_state"]
    supplier = state["supplier_memory"]
    playbook = state["playbook"]
    ask = deal.supplier_ask

    trade_options = []
    raw = deal.metadata.get("trade_options", [])
    if isinstance(raw, list):
        for item in raw:
            try:
                trade_options.append(TradeOption.model_validate(item))
            except Exception:
                pass

    summary = []
    extracted = []
    risks = []
    questions = []

    # Short term explanations are embedded in text (you requested this style)
    summary.append(f"Supplier: {deal.supplier_name} (WTG+LTSA: Wind Turbine Generator + Long-Term Service Agreement).")

    if ask:
        summary.append(f"Detected intent: {ask.intent.value.replace('_', ' ')}.")
        if ask.reason:
            summary.append(f"Stated reason: {ask.reason}.")

        if ask.headline_price_change_pct:
            extracted.append(f"Requested uplift: {ask.headline_price_change_pct.value:.1f}% (supported by email snippet evidence).")
        if ask.deadline:
            extracted.append(f"Deadline signal: {ask.deadline.isoformat()} (if confirmed in text).")
        if ask.requested_trades:
            extracted.append("Requested trades/terms: " + "; ".join(ask.requested_trades))

        if ask.raw_snippets:
            extracted.append("Evidence snippets: " + " | ".join(ask.raw_snippets[:2]))

    # Policy flags (simple MVP gates)
    thresholds = playbook.get("policy_thresholds", {})
    approval_uplift = thresholds.get("price_uplift_pct_requires_internal_approval", 5.0)

    if ask and ask.headline_price_change_pct and ask.headline_price_change_pct.value > float(approval_uplift):
        risks.append(
            f"Approval flag: uplift > {approval_uplift}% threshold → internal approval likely required before committing."
        )

    # Supplier behavior reminders (stateful value)
    if supplier.typical_tactics:
        summary.append("Supplier typical tactics: " + "; ".join(supplier.typical_tactics[:2]) + ".")

    recommended = "Propose a value-based counter with a bundled trade (give/get) and request supporting cost/indexation transparency if missing."

    questions.append("Can you share a breakdown for the uplift drivers (materials/logistics/labor) and whether an indexation mechanism could replace part of the fixed uplift?")
    questions.append("Please confirm whether the deadline relates to manufacturing slot reservation and what flexibility exists on delivery window once the slot is secured.")

    coach = CoachNotes(
        summary=summary,
        extracted_facts=extracted,
        risks_and_flags=risks,
        recommended_next_move=recommended,
        trade_options=trade_options,
        questions_to_ask_supplier=questions,
    )

    state["coach_notes"] = coach
    return state
