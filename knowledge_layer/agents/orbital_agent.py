"""
orbital_agent.py
----------------
Orbital Analysis Agent — Tool only, NO LLM.

Reads from MOSIPState (satellite_data, orbital_data, congestion_data)
and produces a structured orbital analysis dict.

Answers:
  - What orbit is this object in?
  - How crowded is this region?
  - What is the expected orbital lifetime?
  - What are the key orbital characteristics?
"""

from datetime import datetime
from knowledge_layer.agents.state import MOSIPState


# ── Orbital lifetime lookup table (rough estimates) ───────────────────────────
# Based on atmospheric drag and altitude (years)
ORBITAL_LIFETIME = {
    "VLEO":    (0.0, 2.0),    # < 300 km: days to 2 years
    "LEO":     (2.0, 100.0),  # 300-2000 km: 2-100+ years
    "MEO":     (100.0, None), # thousands of years
    "GEO":     (None, None),  # indefinite without disposal
    "HEO":     (None, None),  # indefinite
    "UNKNOWN": (None, None),
}

# Congestion thresholds (number of objects within ±100km shell)
CONGESTION_LEVELS = {
    (0, 10):   "LOW",
    (10, 50):  "MODERATE",
    (50, 200): "HIGH",
    (200, 99999): "EXTREME",
}


def _estimate_lifetime(orbit_type: str, altitude_km: float) -> str:
    """Rough atmospheric lifetime estimate."""
    if orbit_type == "VLEO" or (altitude_km and altitude_km < 200):
        return "< 1 year (rapid decay expected)"
    if altitude_km and altitude_km < 400:
        return "1–5 years (significant drag)"
    if altitude_km and altitude_km < 600:
        return "5–25 years"
    if altitude_km and altitude_km < 800:
        return "25–100 years"
    if orbit_type == "LEO" and altitude_km and altitude_km >= 800:
        return "> 100 years (natural deorbit unlikely)"
    if orbit_type == "GEO":
        return "Indefinite — requires active disposal to graveyard orbit"
    if orbit_type == "MEO":
        return "Centuries — no natural decay"
    return "Unknown"


def _congestion_level(neighbor_count: int) -> str:
    for (lo, hi), label in CONGESTION_LEVELS.items():
        if lo <= neighbor_count < hi:
            return label
    return "UNKNOWN"


def _orbital_characteristics(orbital: dict) -> list[str]:
    """Plain-English list of orbital characteristics."""
    characteristics = []
    inc = orbital.get("inclination")
    ecc = orbital.get("eccentricity", 0) or 0
    alt = orbital.get("altitude_km")
    orbit_type = orbital.get("orbit_type", "")

    if inc is not None:
        if 95 <= inc <= 100:
            characteristics.append("Sun-synchronous orbit (SSO) — high encounter rate with other SSO satellites")
        elif inc >= 85:
            characteristics.append("Near-polar orbit — crosses all latitude bands")
        elif inc <= 10:
            characteristics.append("Equatorial orbit — concentrated in equatorial belt")
        else:
            characteristics.append(f"Mid-inclination orbit ({inc:.1f}°)")

    if ecc > 0.1:
        characteristics.append(f"High eccentricity ({ecc:.4f}) — sweeps through multiple orbital shells per revolution")
    elif ecc > 0.01:
        characteristics.append(f"Moderately elliptical orbit (e={ecc:.4f})")
    else:
        characteristics.append("Near-circular orbit")

    if orbit_type == "GEO":
        characteristics.append("Geostationary orbit — requires graveyard disposal")
    if orbit_type == "VLEO" and alt and alt < 300:
        characteristics.append("Very low orbit — subject to strong atmospheric drag, rapid decay")

    return characteristics


def run_orbital_agent(state: MOSIPState) -> dict:
    """
    Orbital Analysis Agent node.
    Adds 'orbital_analysis' and appends to 'agent_timeline'.
    """
    orbital     = state.get("orbital_data", {})
    congestion  = state.get("congestion_data", {})
    satellite   = state.get("satellite_data", {})

    orbit_type  = orbital.get("orbit_type", "UNKNOWN")
    altitude    = orbital.get("altitude_km")
    neighbor_ct = congestion.get("neighbor_count", 0)

    analysis = {
        "orbit_type":             orbit_type,
        "altitude_km":            altitude,
        "apogee_km":              orbital.get("apogee_km"),
        "perigee_km":             orbital.get("perigee_km"),
        "period_minutes":         orbital.get("period_minutes"),
        "semi_major_axis_km":     orbital.get("semi_major_axis"),
        "inclination_deg":        orbital.get("inclination"),
        "eccentricity":           orbital.get("eccentricity"),
        "raan_deg":               orbital.get("raan"),
        "arg_of_perigee_deg":     orbital.get("arg_of_perigee"),
        "orbital_regime":         orbit_type,
        "congestion_level":       _congestion_level(neighbor_ct),
        "neighbor_count_100km":   neighbor_ct,
        "orbital_lifetime_estimate": _estimate_lifetime(orbit_type, altitude),
        "orbital_characteristics":   _orbital_characteristics(orbital),
        "high_risk_neighbors":    congestion.get("high_risk_neighbors", []),
    }

    timeline_entry = {
        "agent":     "Orbital Analysis Agent",
        "status":    "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "summary":   (
            f"Orbit: {orbit_type} @ {altitude:.0f} km | "
            f"Congestion: {analysis['congestion_level']} ({neighbor_ct} neighbors)"
        ) if altitude else f"Orbit: {orbit_type} — altitude unavailable",
    }

    return {
        "orbital_analysis": analysis,
        "agent_timeline": state.get("agent_timeline", []) + [timeline_entry],
    }
