from __future__ import annotations

import streamlit as st
from typing import Optional

from owpa.schemas.supplier_memory import SupplierMemory


def render_supplier_memory_panel(supplier: Optional[SupplierMemory]) -> None:
    st.subheader("Supplier Memory (stateful)")

    if supplier is None:
        st.info("No supplier memory loaded yet. Run one round to load the supplier profile.")
        return

    # Header
    st.markdown(f"**Supplier:** {supplier.name}")
    st.caption(
        "This is synthetic, structured memory for the MVP. It is used to predict which trade-offs are likely to work."
    )

    # Style + tactics
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"**Style:** `{supplier.style}`")
    with c2:
        st.markdown(f"**Supplier ID:** `{supplier.supplier_id}`")

    if supplier.typical_tactics:
        with st.expander("Typical tactics", expanded=True):
            for t in supplier.typical_tactics:
                st.write(f"- {t}")

    # Movement preferences
    prefs = supplier.movement_preferences
    with st.expander("Movement preferences (0..1)", expanded=True):
        st.caption("Higher means the supplier is more likely to move on that lever in negotiations.")
        st.write(f"- **Price:** {prefs.price:.2f}")
        st.write(f"- **Payment terms:** {prefs.payment_terms:.2f}")
        st.write(f"- **Warranty / liability:** {prefs.warranty_liability:.2f}")
        st.write(f"- **Schedule / slots:** {prefs.schedule_slots:.2f}")
        st.write(f"- **Service scope:** {prefs.service_scope:.2f}")

        # Simple lever recommendation: top 2 by weight
        weights = {
            "payment terms": prefs.payment_terms,
            "service scope": prefs.service_scope,
            "price mechanism (indexation / uplift structure)": prefs.price,
            "warranty / liability": prefs.warranty_liability,
            "schedule / slot flexibility": prefs.schedule_slots,
        }
        top = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:2]
        st.markdown("**Suggested negotiation levers:**")
        for k, v in top:
            st.write(f"- {k} (score {v:.2f})")

    # What worked before
    if supplier.successful_trades:
        with st.expander("Previously successful trades", expanded=False):
            for tr in supplier.successful_trades:
                st.write(f"- {tr}")

    if supplier.sensitive_points:
        with st.expander("Sensitive points (watch-outs)", expanded=False):
            for sp in supplier.sensitive_points:
                st.write(f"- {sp}")

    # Episodes
    with st.expander("Negotiation episodes (history)", expanded=False):
        st.caption("A few past negotiation outcomes that drive the MVP prediction logic.")
        episodes = supplier.episodes[-10:]  # show up to last 10
        for ep in reversed(episodes):
            title = f"{ep.year or 'n/a'} • {ep.outcome.upper()} • {ep.context}"
            st.markdown(f"**{title}**")
            if ep.supplier_opening_ask_pct is not None or ep.settled_pct is not None:
                st.write(
                    f"- Opening ask: {ep.supplier_opening_ask_pct if ep.supplier_opening_ask_pct is not None else 'n/a'}% "
                    f"→ Settled: {ep.settled_pct if ep.settled_pct is not None else 'n/a'}%"
                )
            if ep.primary_trade_used:
                st.write(f"- Primary trade used: {ep.primary_trade_used}")
            if ep.notes:
                st.write(f"- Notes: {ep.notes}")
            st.divider()