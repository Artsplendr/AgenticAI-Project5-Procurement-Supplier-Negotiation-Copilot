from __future__ import annotations

from datetime import datetime

from owpa.agent.state import AgentState
from owpa.config import load_config
from owpa.data.storage import JsonlDealStateStore


def persist_state_node(state: AgentState) -> AgentState:
    cfg = load_config()
    store = JsonlDealStateStore(cfg.state_store_path)

    deal = state["deal_state"]
    deal.round_number += 1
    deal.last_updated_at = datetime.utcnow()

    store.append(deal)
    state["deal_state"] = deal
    return state
