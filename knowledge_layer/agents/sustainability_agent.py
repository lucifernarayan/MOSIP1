"""
sustainability_agent.py
-----------------------
Sustainability Agent — Tool computation + LLM narrative.

Computes:
  1. Orbital Footprint Score (how much space/environment does this object occupy)
  2. Environmental Burden Index (long-term debris contribution)
  3. Congestion Impact (how much does this object add to orbital congestion)
  4. Sustainability Index (0-100, higher = more sustainable)

Then uses LLM to generate a 2-3 sentence sustainability narrative.

Answers:
  - How sustainable is this mission?
  - What is the orbital burden of this object?
  - How does it affect the orbital ecosystem?
"""

from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from backend.config import GROQ_API_KEY, GROQ_MODEL
from knowledge_layer.agents.state import MOSIPState


# Congestion weight per orbit type (how crowded is this regime)
ORBIT_CONGESTION_WEIGHT = {
    "VLEO":    0.7,
    "LEO":     1.0,   # Most critical
    "MEO":     0.5,
    "GEO":     0.8,   # High strategic value
    "HEO":     0.3,
    "UNKNOWN": 0.5,
}

# Lifetime burden weight (longer lifetime = higher burden on ecosystem)
def _lifetime_burden(lifetime_str: str) -> float:
    """Estimate lifetime burden from the estimate string."""
    lt = (lifetime_str or "").lower()
    if "indefinite" in lt or "centuries" in lt or "> 100" in lt:
        return 1.0
    if "25–100" in lt or "25-100" in lt:
        return 0.7
    if "5–25" in lt or "5-25" in lt:
        return 0.4
    if "1–5" in lt or "1-5" in lt:
        return 0.2
    if "< 1" in lt or "rapid" in lt:
        return 0.05
    return 0.5


def _orbital_footprint_score(orbital: dict, congestion: dict) -> float:
    """
    Orbital footprint: combination of altitude band congestion
    and eccentricity (sweeps larger volume if eccentric).
    Returns 0-40 score (higher = larger footprint).
    """
    orbit_type = orbital.get("orbit_type", "UNKNOWN")
    ecc        = orbital.get("eccentricity", 0) or 0
    weight     = ORBIT_CONGESTION_WEIGHT.get(orbit_type, 0.5)
    neighbors  = congestion.get("neighbor_count", 0)

    congestion_factor = min(neighbors / 200, 1.0)   # normalise to 0-1
    ecc_factor        = min(ecc * 5, 1.0)           # high ecc → larger sweep

    footprint = (weight * 20) + (congestion_factor * 15) + (ecc_factor * 5)
    return round(min(footprint, 40), 2)


def _environmental_burden(risk: dict, orbital: dict, lifetime_str: str) -> float:
    """
    Environmental burden: combines risk score + lifetime contribution.
    Returns 0-40 score (higher = more harmful to ecosystem).
    """
    risk_score     = (risk.get("risk_score", 0) or 0) / 100  # normalise
    lifetime_w     = _lifetime_burden(lifetime_str)
    debris_risk    = (risk.get("debris_risk", 0) or 0) / 30  # normalise

    burden = (risk_score * 20) + (lifetime_w * 12) + (debris_risk * 8)
    return round(min(burden, 40), 2)


def _sustainability_index(footprint: float, burden: float) -> int:
    """
    Sustainability Index: 0 = most harmful, 100 = most sustainable.
    Inverts footprint+burden into a positive score.
    """
    raw = footprint + burden         # 0-80
    index = max(0, 100 - int(raw * 1.25))
    return index


def run_sustainability_agent(state: MOSIPState) -> dict:
    """
    Sustainability Agent node.
    Adds 'sustainability_analysis' and appends to 'agent_timeline'.
    """
    orbital     = state.get("orbital_data", {})
    risk        = state.get("risk_data", {})
    congestion  = state.get("congestion_data", {})
    orbital_an  = state.get("orbital_analysis", {})
    population  = state.get("population_data", {})
    satellite   = state.get("satellite_data", {})

    lifetime_str = orbital_an.get("orbital_lifetime_estimate", "Unknown")
    orbit_type   = orbital.get("orbit_type", "UNKNOWN")

    # ── Compute scores ────────────────────────────────────────────────────────
    footprint = _orbital_footprint_score(orbital, congestion)
    burden    = _environmental_burden(risk, orbital, lifetime_str)
    index     = _sustainability_index(footprint, burden)

    if index >= 75:
        sustainability_level = "SUSTAINABLE"
    elif index >= 50:
        sustainability_level = "MODERATELY_SUSTAINABLE"
    elif index >= 25:
        sustainability_level = "CONCERNING"
    else:
        sustainability_level = "UNSUSTAINABLE"

    # ── LLM narrative ─────────────────────────────────────────────────────────
    narrative = ""
    try:
        llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL,
                       temperature=0.3, max_tokens=300)

        prompt = f"""
Satellite: {satellite.get("object_name", "Unknown")} in {orbit_type}
Sustainability Index: {index}/100 ({sustainability_level})
Orbital Lifetime: {lifetime_str}
Orbital Footprint Score: {footprint}/40 (higher = larger environmental footprint)
Environmental Burden Score: {burden}/40 (higher = more harmful)
Neighbor count in ±100km shell: {congestion.get("neighbor_count", 0)}
Risk Level: {risk.get("risk_level", "UNKNOWN")}

Write a 2-3 sentence sustainability narrative for this satellite.
Focus on: what makes this mission sustainable or unsustainable, the long-term orbital ecosystem impact.
Be specific and technical. No bullet points — flowing sentences only.
"""
        msg = llm.invoke([
            SystemMessage(content="You are a space sustainability expert. Write concise, technical assessments."),
            HumanMessage(content=prompt),
        ])
        narrative = msg.content.strip()
    except Exception as e:
        narrative = (
            f"Sustainability Index: {index}/100. "
            f"This {orbit_type} satellite contributes an orbital footprint score of {footprint:.1f}/40 "
            f"and an environmental burden of {burden:.1f}/40. "
            f"LLM narrative unavailable: {str(e)[:80]}"
        )

    analysis = {
        "sustainability_index":    index,
        "sustainability_level":    sustainability_level,
        "orbital_footprint_score": footprint,
        "environmental_burden":    burden,
        "orbital_lifetime":        lifetime_str,
        "orbit_type":              orbit_type,
        "congestion_contribution": congestion.get("neighbor_count", 0),
        "narrative":               narrative,
        "score_breakdown": {
            "footprint_score":      f"{footprint}/40",
            "burden_score":         f"{burden}/40",
            "sustainability_index": f"{index}/100",
        },
        "population_context": {
            "total_tracked":   population.get("total_satellites", 0),
            "orbit_dist":      population.get("orbit_distribution", {}),
            "avg_risk":        population.get("average_risk_score", 0),
        },
    }

    timeline_entry = {
        "agent":     "Sustainability Agent",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": (
            f"Sustainability: {index}/100 ({sustainability_level}) | "
            f"Footprint: {footprint:.1f} | Burden: {burden:.1f}"
        ),
    }

    return {
        "sustainability_analysis": analysis,
        "agent_timeline": state.get("agent_timeline", []) + [timeline_entry],
    }
