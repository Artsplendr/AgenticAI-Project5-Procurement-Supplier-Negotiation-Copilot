from __future__ import annotations

from langgraph.graph import END, StateGraph

from owpa.agent.state import AgentState
from owpa.agent.nodes.ingest import ingest_node
from owpa.agent.nodes.classify import classify_node
from owpa.agent.nodes.extract import extract_node
from owpa.agent.nodes.load_memory import load_memory_node
from owpa.agent.nodes.predict_trade import predict_trade_node
from owpa.agent.nodes.coach import coach_node
from owpa.agent.nodes.draft_email import draft_email_node
from owpa.agent.nodes.persist_state import persist_state_node


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("ingest", ingest_node)
    g.add_node("classify", classify_node)
    g.add_node("extract", extract_node)
    g.add_node("load_memory", load_memory_node)
    g.add_node("predict_trade", predict_trade_node)
    g.add_node("coach", coach_node)
    g.add_node("draft_email", draft_email_node)
    g.add_node("persist_state", persist_state_node)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "classify")
    g.add_edge("classify", "extract")
    g.add_edge("extract", "load_memory")
    g.add_edge("load_memory", "predict_trade")
    g.add_edge("predict_trade", "coach")
    g.add_edge("coach", "draft_email")
    g.add_edge("draft_email", "persist_state")
    g.add_edge("persist_state", END)

    return g.compile()
