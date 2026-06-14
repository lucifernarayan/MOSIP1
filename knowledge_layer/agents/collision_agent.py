"""
collision_agent.py
------------------
Collision Risk Agent — Tool only, NO LLM.

Reads risk_data + orbital_analysis from MOSIPState.
Explains *why* the risk score is what it is.

Answers:
  - Why is collision risk high/low?
  - What are the primary risk drivers?
  - What is the component breakdown?
  - How does this compare to population average?
"""

from datetime import datetime
from knowledge_layer.agents.state import MOSIPState


# Risk component thresholds for interpretation
COMPONENT_THRESHOLDS = {
    "collision_risk": [
        (25, "CRITICAL", "Active conjunction events detected — immediate action required"),
        (15, "HIGH",     "Elevated conjunction frequency in this orbital shell"),
        (5,  "MODERATE", "Some conjunction activity — monitoring recommended"),
        (0,  "LOW",      "Minimal conjunction activity reported"),
    ],
    "debris_risk": [
        (25, "CRITICAL", "Extreme debris density — Kessler cascade risk region"),
        (20, "HIGH",     "High debris density shell — collision probability elevated"),
        (12, "MODERATE", "Moderate background debris density"),
        (0,  "LOW",      "Low debris density region"),
    ],
    "altitude_risk": [
        (35, "HIGH",     "Altitude regime has highest object population density"),
        (20, "MODERATE", "Significant traffic in this altitude band"),
        (10, "LOW",      "Relatively sparse altitude region"),
        (0,  "MINIMAL",  "Low-traffic altitude region"),
    ],
}


def _interpret_component(component: str, score: float) -> tuple[str, str]:
    """Return (level, explanation) for a risk component score."""
    for threshold, level, explanation in COMPONENT_THRESHOLDS.get(component, []):
        if score >= threshold:
            return level, explanation
    return "UNKNOWN", "Insufficient data"


def _risk_context(risk_level: str, orbit_type: str) -> str:
    """Contextual sentence about what this risk means for this orbit."""
    contexts = {
        ("CRITICAL", "LEO"):  "CRITICAL in LEO: Object is in the most debris-dense region of near-Earth space. Probability of collision with catalogued or uncatalogued debris is significantly elevated.",
        ("HIGH",     "LEO"):  "HIGH in LEO: Object faces considerable collision risk from debris fragments and other satellites in this crowded regime.",
        ("CRITICAL", "GEO"):  "CRITICAL in GEO: Geostationary band congestion is a long-term sustainability concern. Disposal to graveyard orbit is essential.",
        ("HIGH",     "GEO"):  "HIGH in GEO: Geostationary slot and proximity operations require careful conjunction screening.",
        ("MEDIUM",   "MEO"):  "MEDIUM in MEO: GPS/GLONASS/Galileo belt has moderate debris density. Some long-lived debris from historical breakup events.",
        ("LOW",      "GEO"):  "LOW in GEO: Object maintains safe separation from active assets. Graveyard disposal planning still required.",
    }
    return contexts.get(
        (risk_level, orbit_type),
        f"{risk_level} risk in {orbit_type}: Object requires standard monitoring protocols."
    )


def run_collision_agent(state: MOSIPState) -> dict:
    """
    Collision Risk Agent node.
    Adds 'collision_analysis' and appends to 'agent_timeline'.
    """
    risk        = state.get("risk_data", {})
    orbital     = state.get("orbital_data", {})
    population  = state.get("population_data", {})
    congestion  = state.get("congestion_data", {})

    score       = risk.get("risk_score", 0) or 0
    level       = risk.get("risk_level", "UNKNOWN")
    drivers     = risk.get("risk_drivers", [])
    orbit_type  = orbital.get("orbit_type", "UNKNOWN")

    col_score = risk.get("collision_risk", 0) or 0
    deb_score = risk.get("debris_risk", 0) or 0
    alt_score = risk.get("altitude_risk", 0) or 0

    col_level, col_exp = _interpret_component("collision_risk", col_score)
    deb_level, deb_exp = _interpret_component("debris_risk", deb_score)
    alt_level, alt_exp = _interpret_component("altitude_risk", alt_score)

    avg_risk = population.get("average_risk_score", 0) or 0
    relative  = "above average" if score > avg_risk else "below average"

    analysis = {
        "overall": {
            "risk_score":  score,
            "risk_level":  level,
            "context":     _risk_context(level, orbit_type),
            "vs_population": f"{score:.1f} vs population average {avg_risk:.1f} — {relative}",
        },
        "components": {
            "collision_risk": {
                "score":       col_score,
                "level":       col_level,
                "explanation": col_exp,
            },
            "debris_risk": {
                "score":       deb_score,
                "level":       deb_level,
                "explanation": deb_exp,
            },
            "altitude_risk": {
                "score":       alt_score,
                "level":       alt_level,
                "explanation": alt_exp,
            },
        },
        "primary_drivers":   drivers,
        "congestion_context": {
            "objects_in_shell":   congestion.get("neighbor_count", 0),
            "high_risk_count":    congestion.get("high_risk_count", 0),
            "congestion_level":   state.get("orbital_analysis", {}).get("congestion_level", "UNKNOWN"),
        },
        "score_breakdown": {
            "collision_component": f"{col_score:.1f} / 30",
            "debris_component":    f"{deb_score:.1f} / 30",
            "altitude_component":  f"{alt_score:.1f} / 40",
            "total":               f"{score:.1f} / 100",
        },
    }

    summary_line = (
        f"Risk Score: {score:.1f} ({level}) | "
        f"Collision: {col_score:.1f} | Debris: {deb_score:.1f} | "
        f"Altitude: {alt_score:.1f} | {relative}"
    )

    timeline_entry = {
        "agent":     "Collision Risk Agent",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary":   summary_line,
    }

    return {
        "collision_analysis": analysis,
        "agent_timeline": state.get("agent_timeline", []) + [timeline_entry],
    }
