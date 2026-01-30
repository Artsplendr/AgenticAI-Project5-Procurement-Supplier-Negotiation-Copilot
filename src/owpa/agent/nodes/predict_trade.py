from __future__ import annotations

from owpa.agent.state import AgentState
from owpa.schemas.outputs import TradeOption


def _similarity_score(intent: str, episode_context: str) -> float:
    # Tiny heuristic: context match boosts; in later versions we can embed or do better matching.
    c = episode_context.lower()
    s = 0.0
    if "wtg+ltsa" in c or "wtg" in c or "ltsa" in c:
        s += 0.2
    if "north sea" in c:
        s += 0.1
    if intent == "price_increase_request" and ("ask" in c or "uplift" in c or "increase" in c):
        s += 0.1
    return min(0.5, s)


def predict_trade_node(state: AgentState) -> AgentState:
    supplier = state["supplier_memory"]
    deal = state["deal_state"]
    ask = deal.supplier_ask

    if ask is None:
        state["deal_state"].metadata["prediction_note"] = "No supplier ask available."
        return state

    # Candidate trades (MVP) – deliberately small and explainable
    candidates = [
        ("earlier milestone payment (improve cashflow)", "reduce headline uplift"),
        ("extend LTSA term by 2 years", "reduce headline uplift"),
        ("accept capped indexation (cap/floor + transparency)", "reduce base uplift now"),
        ("bundle critical spares package", "reduce service uplift / improve availability terms"),
        ("adjust delay LDs structure to capped LD + recovery plan (LDs = Liquidated Damages)", "reduce uplift / confirm slot")
    ]

    # Leverage supplier movement preferences to score acceptance
    prefs = supplier.movement_preferences

    def base_accept(we_offer: str) -> float:
        o = we_offer.lower()
        if "payment" in o:
            return prefs.payment_terms
        if "ltsa" in o or "term" in o:
            return prefs.service_scope
        if "indexation" in o:
            return prefs.price  # often linked to price mechanism
        if "spares" in o or "service" in o:
            return prefs.service_scope
        if "ld" in o or "schedule" in o or "slot" in o:
            return prefs.schedule_slots
        return 0.35

    # Episode reinforcement: if a trade appears in history, boost
    history_text = " ".join([e.primary_trade_used or "" for e in supplier.episodes]).lower()

    options = []
    for offer, request in candidates:
        p = base_accept(offer)

        if offer.lower() in history_text:
            p += 0.10

        # intent shaping: if they are pressuring on slot, schedule trades become more plausible
        if ask.intent.value == "slot_pressure_deadline" and ("ld" in offer.lower() or "schedule" in offer.lower()):
            p += 0.10

        # cap to [0, 1]
        p = max(0.05, min(0.95, p))

        rationale = []
        rationale.append(f"Supplier movement preference suggests this lever is negotiable (based on stored profile).")
        # Add a couple episode-based rationales
        for ep in supplier.episodes[:3]:
            if ep.primary_trade_used and any(tok in ep.primary_trade_used.lower() for tok in offer.lower().split()[:2]):
                rationale.append(f"Similar trade appeared in prior negotiation context: '{ep.context}'.")
                break

        options.append(
            TradeOption(
                we_offer=offer,
                we_request=request,
                predicted_acceptance=round(p, 2),
                rationale=rationale[:3],
            )
        )

    # pick top 2–3 options
    options = sorted(options, key=lambda x: x.predicted_acceptance, reverse=True)[:3]
    deal.metadata["trade_options_count"] = len(options)
    state["deal_state"] = deal
    state["deal_state"].metadata["trade_options"] = [o.model_dump() for o in options]
    return state
