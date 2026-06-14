"""
orchestrator.py
---------------
MOSIP Multi-Agent Orchestrator — LangGraph Supervisor.

Architecture:
  ┌─────────────────────────────────────────────────────────┐
  │  MOSIP LangGraph Pipeline                               │
  │                                                          │
  │  START → [gather] → [orbital] → [collision] →           │
  │          [compliance] → [sustainability] →               │
  │          [forecast] → [mitigation] → [documentation]    │
  │          → END                                           │
  └─────────────────────────────────────────────────────────┘

Each node:
  - Reads from shared MOSIPState
  - Writes its results back into MOSIPState
  - Appends a timeline entry

The 'gather' node = Phase 1 unified intelligence layer
(connects PostgreSQL + Qdrant before agents run)
"""

from datetime import datetime
from typing import Any

from langgraph.graph import StateGraph, END

from knowledge_layer.agents.state import MOSIPState
from knowledge_layer.agents.orbital_agent       import run_orbital_agent
from knowledge_layer.agents.collision_agent     import run_collision_agent
from knowledge_layer.agents.compliance_agent    import run_compliance_agent
from knowledge_layer.agents.sustainability_agent import run_sustainability_agent
from knowledge_layer.agents.forecast_agent      import run_forecast_agent
from knowledge_layer.agents.mitigation_agent    import run_mitigation_agent
from knowledge_layer.agents.documentation_agent import run_documentation_agent
from backend.intelligence.satellite_intelligence import gather_satellite_intelligence


# ── Gather node: Phase 1 unified intelligence layer ──────────────────────────

def gather_node(state: MOSIPState) -> dict:
    """
    Phase 1 entry point.
    Fetches satellite profile from PostgreSQL and regulations from Qdrant.
    Populates the base fields of MOSIPState before any agent runs.
    """
    norad_id   = state.get("norad_id")
    raw_params = state.get("raw_params", {})

    intel = gather_satellite_intelligence(
        norad_id=norad_id,
        altitude_km=raw_params.get("altitude_km"),
        mean_motion=raw_params.get("mean_motion"),
        eccentricity=raw_params.get("eccentricity"),
        inclination=raw_params.get("inclination"),
        raan=raw_params.get("raan"),
        arg_of_perigee=raw_params.get("arg_of_perigee"),
        debris_density=raw_params.get("debris_density"),
        conjunction_frequency=raw_params.get("conjunction_frequency"),
    )

    if intel.get("error"):
        return {
            "errors":         [intel["error"]],
            "agent_timeline": [{
                "agent":     "Supervisor (Gather)",
                "status":    "error",
                "timestamp": datetime.utcnow().isoformat(),
                "summary":   intel["error"],
            }],
            # Populate empty dicts so downstream nodes don't crash
            "satellite_data":   {},
            "orbital_data":     {},
            "risk_data":        {},
            "congestion_data":  {},
            "regulations":      [],
            "population_data":  {},
        }

    timeline_entry = {
        "agent":     "Supervisor (Gather)",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": (
            f"Loaded {intel['satellite'].get('object_name', 'Unknown')} | "
            f"Orbit: {intel['orbital'].get('orbit_type', '?')} @ {intel['orbital'].get('altitude_km', '?')} km | "
            f"Regulations retrieved: {len(intel['regulations'])}"
        ),
    }

    return {
        "satellite_data":  intel["satellite"],
        "orbital_data":    intel["orbital"],
        "risk_data":       intel["risk"],
        "congestion_data": intel["congestion"],
        "regulations":     intel["regulations"],
        "population_data": intel["population"],
        "errors":          [],
        "agent_timeline":  [timeline_entry],
    }


# ── Wrapper nodes (keep LangGraph state merge correct) ───────────────────────

def orbital_node(state: MOSIPState) -> dict:
    return run_orbital_agent(state)

def collision_node(state: MOSIPState) -> dict:
    return run_collision_agent(state)

def compliance_node(state: MOSIPState) -> dict:
    return run_compliance_agent(state)

def sustainability_node(state: MOSIPState) -> dict:
    return run_sustainability_agent(state)

def forecast_node(state: MOSIPState) -> dict:
    return run_forecast_agent(state)

def mitigation_node(state: MOSIPState) -> dict:
    return run_mitigation_agent(state)

def documentation_node(state: MOSIPState) -> dict:
    return run_documentation_agent(state)


# ── Build the LangGraph graph ─────────────────────────────────────────────────

def _build_mosip_graph() -> StateGraph:
    graph = StateGraph(MOSIPState)

    # Register nodes
    graph.add_node("gather",          gather_node)
    graph.add_node("orbital",         orbital_node)
    graph.add_node("collision",       collision_node)
    graph.add_node("compliance",      compliance_node)
    graph.add_node("sustainability",  sustainability_node)
    graph.add_node("forecast_agent",  forecast_node)
    graph.add_node("mitigation",      mitigation_node)
    graph.add_node("documentation",   documentation_node)

    # Sequential pipeline edges
    graph.set_entry_point("gather")
    graph.add_edge("gather",         "orbital")
    graph.add_edge("orbital",        "collision")
    graph.add_edge("collision",      "compliance")
    graph.add_edge("compliance",     "sustainability")
    graph.add_edge("sustainability",  "forecast_agent")
    graph.add_edge("forecast_agent",  "mitigation")
    graph.add_edge("mitigation",     "documentation")

    graph.add_edge("documentation",  END)

    return graph.compile()


# Compiled graph — import and use this
mosip_graph = _build_mosip_graph()


# ── Public API ────────────────────────────────────────────────────────────────

def run_full_assessment(
    norad_id: int | None = None,
    raw_params: dict | None = None,
) -> dict:
    """
    Run the full MOSIP multi-agent pipeline.

    Args:
        norad_id:   NORAD Catalog ID to load from PostgreSQL
        raw_params: Raw orbital parameters dict for hypothetical analysis

    Returns:
        Complete MOSIPState dict with all agent outputs.
    """
    initial_state: MOSIPState = {
        "norad_id":               norad_id,
        "raw_params":             raw_params or {},
        # Pre-populate empty fields so TypedDict is valid at start
        "satellite_data":         {},
        "orbital_data":           {},
        "risk_data":              {},
        "congestion_data":        {},
        "population_data":        {},
        "regulations":            [],
        "orbital_analysis":       {},
        "collision_analysis":     {},
        "compliance_analysis":    {},
        "sustainability_analysis": {},
        "forecast":               {},
        "recommendations":        [],
        "mitigation_analysis":    {},
        "report":                 "",
        "agent_timeline":         [],
        "errors":                 [],
    }

    final_state = mosip_graph.invoke(initial_state)
    return dict(final_state)


def run_agent_only(
    agent: str,
    norad_id: int | None = None,
    raw_params: dict | None = None,
) -> dict:
    """
    Run only up to a specific agent (useful for partial assessments).

    agent options: "orbital", "collision", "compliance",
                   "sustainability", "forecast", "mitigation", "documentation"
    """
    # Run full pipeline but return only that agent's output key
    full = run_full_assessment(norad_id=norad_id, raw_params=raw_params)

    agent_key_map = {
        "orbital":        "orbital_analysis",
        "collision":      "collision_analysis",
        "compliance":     "compliance_analysis",
        "sustainability": "sustainability_analysis",
        "forecast":       "forecast",
        "mitigation":     "mitigation_analysis",
        "documentation":  "report",
    }

    key = agent_key_map.get(agent, agent)
    return {
        "agent":          agent,
        "norad_id":       norad_id,
        "satellite":      full.get("satellite_data", {}),
        "result":         full.get(key, {}),
        "agent_timeline": [
            e for e in full.get("agent_timeline", [])
            if agent.lower() in e.get("agent", "").lower()
            or "Supervisor" in e.get("agent", "")
        ],
        "errors":         full.get("errors", []),
    }
