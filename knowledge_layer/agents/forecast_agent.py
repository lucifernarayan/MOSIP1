"""
forecast_agent.py
-----------------
Forecast Agent — Tool projections + LLM interpretation.

Tool layer:
  - Computes 5/10/25-year debris population growth estimates
  - Projects collision probability trend
  - Estimates future sustainability state

LLM layer:
  - Interprets what the numbers mean
  - Highlights inflection points and critical thresholds

Answers:
  - What happens if nothing changes?
  - What will collision risk look like in 25 years?
  - When does the orbital environment become critical?
"""

from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from backend.config import GROQ_API_KEY, GROQ_MODEL
from knowledge_layer.agents.state import MOSIPState


# Annual debris growth rate by orbit type (percent per year)
# Based on ESA/IADC 2024 Space Debris Environment Report trends
ANNUAL_DEBRIS_GROWTH = {
    "VLEO":    0.03,   # 3%/yr — partially offset by atmospheric drag
    "LEO":     0.05,   # 5%/yr — driven by mega-constellations
    "MEO":     0.01,   # 1%/yr — relatively stable
    "GEO":     0.02,   # 2%/yr — new slots filling up
    "HEO":     0.01,
    "UNKNOWN": 0.03,
}

# Baseline collision probability per year (rough estimates by orbit type)
BASELINE_COLLISION_PROB = {
    "VLEO":    0.001,
    "LEO":     0.003,
    "MEO":     0.0005,
    "GEO":     0.001,
    "HEO":     0.0002,
    "UNKNOWN": 0.001,
}


def _project_population(orbit_type: str, current_count: int, years: int) -> int:
    """Compound growth projection for object count in this orbital shell."""
    rate = ANNUAL_DEBRIS_GROWTH.get(orbit_type, 0.03)
    projected = int(current_count * ((1 + rate) ** years))
    return projected


def _project_collision_prob(orbit_type: str, risk_score: float, years: int) -> float:
    """
    Annual collision probability projection.
    Scales with debris growth and current risk score.
    """
    base = BASELINE_COLLISION_PROB.get(orbit_type, 0.001)
    growth = ANNUAL_DEBRIS_GROWTH.get(orbit_type, 0.03)
    risk_multiplier = (risk_score / 50.0) if risk_score else 1.0  # normalise around 50

    projected = base * risk_multiplier * ((1 + growth) ** years)
    return round(min(projected, 1.0), 6)


def _kessler_risk(orbit_type: str, current_count: int,
                  projected_5yr: int) -> str:
    """Assess Kessler syndrome risk based on growth trajectory."""
    if orbit_type not in ("LEO", "VLEO"):
        return "Not applicable for this orbit type"
    growth_pct = ((projected_5yr - current_count) / max(current_count, 1)) * 100
    if growth_pct > 30:
        return "HIGH — rapid debris accumulation could trigger cascade events within decades"
    if growth_pct > 15:
        return "MODERATE — concerning growth trajectory; active debris removal needed"
    return "LOW — growth within manageable bounds if disposal compliance improves"


def run_forecast_agent(state: MOSIPState) -> dict:
    """
    Forecast Agent node.
    Adds 'forecast' and appends to 'agent_timeline'.
    """
    orbital     = state.get("orbital_data", {})
    risk        = state.get("risk_data", {})
    congestion  = state.get("congestion_data", {})
    satellite   = state.get("satellite_data", {})
    population  = state.get("population_data", {})

    orbit_type    = orbital.get("orbit_type", "UNKNOWN")
    risk_score    = risk.get("risk_score", 50) or 50
    current_count = congestion.get("neighbor_count", 0)
    total_sats    = population.get("total_satellites", 0)

    # ── Tool-based projections ────────────────────────────────────────────────
    projections = {}
    for years in [5, 10, 25]:
        pop_projected  = _project_population(orbit_type, current_count, years)
        col_prob       = _project_collision_prob(orbit_type, risk_score, years)
        risk_projected = min(100, risk_score * (1 + ANNUAL_DEBRIS_GROWTH.get(orbit_type, 0.03)) ** years)

        projections[f"{years}yr"] = {
            "year":                        datetime.utcnow().year + years,
            "projected_objects_in_shell":  pop_projected,
            "shell_growth_pct":            round(((pop_projected - current_count) / max(current_count, 1)) * 100, 1),
            "projected_collision_prob_per_yr": col_prob,
            "projected_risk_score":        round(risk_projected, 1),
        }

    kessler = _kessler_risk(orbit_type, current_count, projections["5yr"]["projected_objects_in_shell"])

    # ── LLM interpretation ────────────────────────────────────────────────────
    interpretation = ""
    try:
        llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL,
                       temperature=0.3, max_tokens=500)

        prompt = f"""
Satellite orbit: {orbit_type} at {orbital.get("altitude_km", "N/A")} km
Current risk score: {risk_score}/100
Current objects in ±100km shell: {current_count}
Total tracked satellites: {total_sats}

5-year projection:
  - Objects in shell: {projections["5yr"]["projected_objects_in_shell"]}
  - Collision probability/yr: {projections["5yr"]["projected_collision_prob_per_yr"]:.5%}
  - Projected risk score: {projections["5yr"]["projected_risk_score"]}

10-year projection:
  - Objects in shell: {projections["10yr"]["projected_objects_in_shell"]}
  - Collision probability/yr: {projections["10yr"]["projected_collision_prob_per_yr"]:.5%}
  - Projected risk score: {projections["10yr"]["projected_risk_score"]}

25-year projection:
  - Objects in shell: {projections["25yr"]["projected_objects_in_shell"]}
  - Collision probability/yr: {projections["25yr"]["projected_collision_prob_per_yr"]:.5%}
  - Projected risk score: {projections["25yr"]["projected_risk_score"]}

Kessler risk assessment: {kessler}

Write a 3-4 sentence forecast interpretation covering:
1. The trajectory of orbital congestion for this satellite's shell
2. When (if ever) the situation becomes critical
3. What would change the forecast most (e.g., increased compliance, ADR missions)
Be specific and technical. No bullet points.
"""
        msg = llm.invoke([
            SystemMessage(content="You are a space sustainability forecaster. Write concise, data-driven forecasts."),
            HumanMessage(content=prompt),
        ])
        interpretation = msg.content.strip()
    except Exception as e:
        interpretation = (
            f"Forecast computed without LLM. By 2049 ({25} years), "
            f"the {orbit_type} shell is projected to grow by "
            f"{projections['25yr']['shell_growth_pct']:.0f}%. "
            f"Collision probability rises to {projections['25yr']['projected_collision_prob_per_yr']:.4%}/yr. "
            f"LLM unavailable: {str(e)[:80]}"
        )

    forecast = {
        "orbit_type":              orbit_type,
        "baseline_risk_score":     risk_score,
        "kessler_syndrome_risk":   kessler,
        "projections":             projections,
        "interpretation":          interpretation,
        "assumptions": [
            f"Annual debris growth rate: {ANNUAL_DEBRIS_GROWTH.get(orbit_type, 0.03)*100:.1f}%/yr in {orbit_type}",
            "No active debris removal missions assumed",
            "Current disposal compliance rates maintained",
            "Based on ESA/IADC debris environment models",
        ],
    }

    timeline_entry = {
        "agent":     "Forecast Agent",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": (
            f"25yr outlook: Shell grows {projections['25yr']['shell_growth_pct']:.0f}% | "
            f"Collision prob: {projections['25yr']['projected_collision_prob_per_yr']:.4%}/yr | "
            f"Kessler: {kessler[:30]}..."
        ),
    }

    return {
        "forecast": forecast,
        "agent_timeline": state.get("agent_timeline", []) + [timeline_entry],
    }
