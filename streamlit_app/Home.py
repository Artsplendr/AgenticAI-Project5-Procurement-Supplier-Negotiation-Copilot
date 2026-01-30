from __future__ import annotations

import os
import streamlit as st

from owpa.config import load_config
from owpa.data.loader import load_deal_state, load_suppliers_fixture
from owpa.agent.graph import build_graph

from components.supplier_memory_panel import render_supplier_memory_panel

st.set_page_config(page_title="Procurement Supplier Negotiation Copilot", layout="wide")

# Load global styles
def _inject_css(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        # Fail silently if style file not found
        pass

_inject_css("streamlit_app/assets/style.css")

cfg = load_config()

st.title("Procurement Supplier Negotiation Copilot")
st.caption("WTG = Wind Turbine Generator • LTSA = Long-Term Service Agreement • LDs = Liquidated Damages")

# Persist UI data across reruns
if "supplier_memory" not in st.session_state:
    st.session_state["supplier_memory"] = None
if "coach_notes" not in st.session_state:
    st.session_state["coach_notes"] = None
if "email_draft" not in st.session_state:
    st.session_state["email_draft"] = None
if "updated_deal_state" not in st.session_state:
    st.session_state["updated_deal_state"] = None
if "has_results" not in st.session_state:
    st.session_state["has_results"] = False

with st.sidebar:
    st.header("Session")
    st.write("This MVP processes one supplier email per round and keeps state (deal tracker + supplier memory).")

    # Supplier selection (dropdown from fixtures, with robust fallback)
    try:
        _suppliers = load_suppliers_fixture(cfg.suppliers_fixture_path)
        _supplier_names = [s.name for s in _suppliers]
    except Exception:
        _suppliers = []
        _supplier_names = []

    if _supplier_names:
        _default = "Battila Turbines"
        _idx = _supplier_names.index(_default) if _default in _supplier_names else 0
        supplier_name = st.selectbox(
            "Supplier name (must match fixtures)",
            _supplier_names,
            index=_idx,
            help="Choose a supplier from fixtures"
        )
    else:
        supplier_name = st.text_input(
            "Supplier name (must match fixtures)",
            value="Battila Turbines",
            help="Fixtures not loaded; type the name exactly"
        )

    subject = st.text_input("Email subject", value="Commercial update for WTG + LTSA")

    st.subheader("Supplier email input")
    email_text = st.text_area(
        "Paste supplier email text here",
        height=260,
        placeholder="Example: We require a 9% adjustment due to input cost escalation. Please confirm by Friday..."
    )
    run = st.button("Run negotiation round", type="primary", use_container_width=True)

    st.divider()
    st.write("Config (from .env)")
    st.code(
        f"USE_LLM={os.getenv('USE_LLM', 'true')}\nOPENAI_MODEL={cfg.openai_model}",
        language="text"
    )

# Load base DealState and override supplier for demo flexibility
sample_path = os.getenv("SAMPLE_DEAL_STATE_PATH", "./data/fixtures/sample_deal_state.json")
deal = load_deal_state(sample_path)
deal.supplier_name = supplier_name

# Layout: split main area → left = results tabs, right = supplier memory
left_main, right = st.columns([1.4, 1.0])

# We'll fill this after running a round (pull existing from session)
supplier_loaded = st.session_state.get("supplier_memory")
coach = st.session_state.get("coach_notes")
draft = st.session_state.get("email_draft")
updated_deal = st.session_state.get("updated_deal_state")

if run:
    if not email_text.strip():
        st.error("Please paste a supplier email before running.")
        st.stop()

    graph = build_graph()

    result = graph.invoke({
        "email_text": email_text,
        "supplier_email_subject": subject,
        "deal_state": deal
    })

    st.session_state["coach_notes"] = result.get("coach_notes")
    st.session_state["email_draft"] = result.get("email_draft")
    st.session_state["updated_deal_state"] = result.get("deal_state")
    st.session_state["supplier_memory"] = result.get("supplier_memory")
    supplier_loaded = st.session_state["supplier_memory"]
    coach = st.session_state["coach_notes"]
    draft = st.session_state["email_draft"]
    updated_deal = st.session_state["updated_deal_state"]

    st.session_state["has_results"] = True

# Always render last results if available (persists across reruns)
with left_main:
    if st.session_state.get("has_results"):
        t1, t2, t3 = st.tabs(["Coach Notes (internal)", "Trade Prediction", "Email Draft (external)"])

        with t1:
            if coach:
                st.markdown("### Summary")
                st.write("\n".join([f"- {x}" for x in coach.summary]))
                st.markdown("### Extracted facts")
                st.write("\n".join([f"- {x}" for x in coach.extracted_facts]) or "- (none)")
                st.markdown("### Risks & flags")
                st.write("\n".join([f"- {x}" for x in coach.risks_and_flags]) or "- (none)")
                st.markdown("### Recommended next move")
                st.info(coach.recommended_next_move)
                st.markdown("### Questions to ask supplier")
                st.write("\n".join([f"- {x}" for x in coach.questions_to_ask_supplier]) or "- (none)")
            else:
                st.write("No coach notes generated.")

        with t2:
            opts = coach.trade_options if coach else []
            if opts:
                for o in opts:
                    st.markdown(f"**Offer:** {o.we_offer}")
                    st.markdown(f"**Request:** {o.we_request}")
                    st.progress(min(max(o.predicted_acceptance, 0.0), 1.0))
                    st.caption(f"Predicted acceptance: {o.predicted_acceptance:.2f}")
                    if o.rationale:
                        st.write("\n".join([f"- {x}" for x in o.rationale]))
                    st.divider()
            else:
                st.write("No trade options available.")

        with t3:
            if draft:
                st.markdown(f"**Subject:** {draft.subject}")
                st.text_area("Email body (copy/paste)", value=draft.body, height=440)
                if draft.missing_info_disclaimer:
                    st.caption(draft.missing_info_disclaimer)
            else:
                st.write("No email draft generated.")

        # Removed 'Updated DealState' tab per UX request

with right:
    # If we haven't run yet, we can still show an "empty" panel.
    render_supplier_memory_panel(st.session_state.get("supplier_memory"))