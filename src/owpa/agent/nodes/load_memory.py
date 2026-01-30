from __future__ import annotations

from owpa.agent.state import AgentState
from owpa.config import load_config
from owpa.data.loader import get_supplier, load_playbook, load_suppliers_fixture


def load_memory_node(state: AgentState) -> AgentState:
    cfg = load_config()

    suppliers = load_suppliers_fixture(cfg.suppliers_fixture_path)
    playbook = load_playbook(cfg.playbook_path)

    deal = state["deal_state"]
    supplier = get_supplier(suppliers, supplier_name=deal.supplier_name)

    state["supplier_memory"] = supplier
    state["playbook"] = playbook

    # store supplier_id for traceability
    deal.metadata["supplier_id"] = supplier.supplier_id
    state["deal_state"] = deal
    return state
