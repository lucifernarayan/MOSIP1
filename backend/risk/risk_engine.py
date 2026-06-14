import json

# ──────────────────────────────────────────────
# Debris density estimates by orbital shell
# Source: ESA Space Debris Office / NASA ORDEM
# Values represent relative risk weighting (0–30)
# ──────────────────────────────────────────────
DEBRIS_DENSITY_TABLE = {
    "VLEO": 5,   # Very low — objects decay quickly
    "LEO":  30,  # Highest — Kessler syndrome risk zone, Starlink, ISS shells
    "MEO":  12,  # Moderate — GPS / Galileo / GLONASS belts
    "GEO":  8,   # Lower density but graveyard concerns
    "HEO":  4,   # Sparse — highly eccentric orbits
    "UNKNOWN": 10,
}

# Inclination risk bonus (sun-synchronous and polar orbits → higher encounter rates)
def _inclination_risk(inclination: float) -> float:
    if inclination is None:
        return 0.0
    if 95 <= inclination <= 100:    # Sun-synchronous
        return 8.0
    if inclination >= 85:            # Near-polar
        return 5.0
    if inclination <= 10:            # Equatorial
        return 3.0
    return 0.0


# Eccentricity risk bonus (higher e → sweeps through multiple shells)
def _eccentricity_risk(eccentricity: float) -> float:
    if eccentricity is None:
        return 0.0
    if eccentricity > 0.5:
        return 12.0
    if eccentricity > 0.1:
        return 6.0
    if eccentricity > 0.01:
        return 2.0
    return 0.0


def calculate_risk(
    orbit_type: str,
    altitude_km: float = None,
    inclination: float = None,
    eccentricity: float = None,
    debris_density: float = None,       # override from external source
    conjunction_frequency: float = None,
) -> dict:
    """
    Calculate a structured risk profile for a satellite.

    Returns:
        {
            "risk_score":       float (0–100),
            "risk_level":       str   (LOW / MEDIUM / HIGH / CRITICAL),
            "collision_risk":   float,
            "debris_risk":      float,
            "altitude_risk":    float,
            "risk_drivers":     list[str],
        }
    """
    drivers = []

    # ── Altitude / orbit-type base score ─────────────────────────────────────
    base_by_orbit = {
        "VLEO":    35,   # short lifetime but very dense traffic (Starlink)
        "LEO":     40,
        "MEO":     20,
        "GEO":     10,
        "HEO":     15,
        "UNKNOWN": 20,
    }
    altitude_risk = base_by_orbit.get(orbit_type, 20)

    if orbit_type in ("LEO", "VLEO"):
        drivers.append(f"Object in {orbit_type} — highest debris density region")

    # ── Debris density ────────────────────────────────────────────────────────
    if debris_density is not None:
        debris_risk = min(debris_density, 30)
    else:
        debris_risk = DEBRIS_DENSITY_TABLE.get(orbit_type, 10)

    if debris_risk >= 20:
        drivers.append("High local debris density in this orbital shell")

    # ── Conjunction frequency (from external CDM data if available) ───────────
    collision_risk = 0.0
    if conjunction_frequency is not None:
        collision_risk = min(conjunction_frequency, 30)
        if collision_risk >= 15:
            drivers.append(f"High conjunction frequency: {conjunction_frequency:.1f}/week")

    # ── Inclination bonus ─────────────────────────────────────────────────────
    inc_bonus = _inclination_risk(inclination)
    if inc_bonus >= 5:
        drivers.append(f"High-inclination orbit ({inclination:.1f}°) → elevated encounter rate")

    # ── Eccentricity bonus ────────────────────────────────────────────────────
    ecc_bonus = _eccentricity_risk(eccentricity)
    if ecc_bonus >= 6:
        drivers.append(f"High eccentricity ({eccentricity:.4f}) → sweeps multiple orbital shells")

    # ── Final score ───────────────────────────────────────────────────────────
    raw_score = altitude_risk + debris_risk + collision_risk + inc_bonus + ecc_bonus
    risk_score = round(min(raw_score, 100), 2)

    # ── Risk level thresholds ─────────────────────────────────────────────────
    if risk_score >= 75:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score":     risk_score,
        "risk_level":     risk_level,
        "collision_risk": round(collision_risk, 2),
        "debris_risk":    round(debris_risk, 2),
        "altitude_risk":  round(altitude_risk, 2),
        "risk_drivers":   drivers,
    }


def risk_level_from_score(score: float) -> str:
    """Utility — convert numeric score to label."""
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    return "LOW"