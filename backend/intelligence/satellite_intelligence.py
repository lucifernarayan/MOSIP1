"""
satellite_intelligence.py
--------------------------
Phase 1: Unified Intelligence Layer

The foundation for every MOSIP agent.

Given a norad_id (or raw orbital params), it:
  1. Queries PostgreSQL → satellite profile + risk
  2. Generates contextual compliance queries from the orbital data
  3. Searches Qdrant → retrieves applicable regulatory chunks
  4. Returns a unified intelligence context dict

This context is passed into MOSIPState and consumed by all agents.
No LLM call happens here — this is pure data retrieval and structuring.
"""

import json
from knowledge_layer.db_service import (
    get_satellite_profile,
    get_orbit_neighbors,
    get_high_risk_neighbors,
    get_population_metrics,
)
from knowledge_layer.rag_service import get_applicable_regulations
from backend.risk.orbit_classifier import compute_all_orbital_elements
from backend.risk.risk_engine import calculate_risk


def gather_satellite_intelligence(
    norad_id: int | None = None,
    # raw orbital params (used when norad_id not available)
    altitude_km: float | None = None,
    mean_motion: float | None = None,
    eccentricity: float | None = None,
    inclination: float | None = None,
    raan: float | None = None,
    arg_of_perigee: float | None = None,
    debris_density: float | None = None,
    conjunction_frequency: float | None = None,
) -> dict:
    """
    Unified intelligence context builder.

    Returns:
    {
        "satellite":        { ...PostgreSQL profile or computed data },
        "orbital":          { altitude, orbit_type, apogee, perigee, ... },
        "risk":             { score, level, drivers, components },
        "congestion":       { neighbor_count, high_risk_neighbors, ... },
        "regulations":      [ { source, document, score, text }, ... ],
        "population":       { total, orbit_dist, risk_dist, avg_risk },
        "source":           "database" | "raw_input",
        "error":            None | str
    }
    """

    # ── Step 1: Fetch or compute satellite + orbital + risk data ─────────────
    satellite = {}
    orbital   = {}
    risk      = {}
    source    = "database"

    if norad_id is not None:
        profile = get_satellite_profile(norad_id)
        if not profile:
            return {
                "error": f"Satellite NORAD {norad_id} not found in database.",
                "satellite": {}, "orbital": {}, "risk": {},
                "congestion": {}, "regulations": [], "population": {},
            }

        # Extract orbital elements from profile
        satellite = {
            "norad_id":    profile.get("norad_id"),
            "object_name": profile.get("object_name", "Unknown"),
            "object_id":   profile.get("object_id"),
            "epoch_time":  str(profile.get("epoch_time", "")),
            "id":          profile.get("id"),
        }

        # Prefer precomputed orbital params; fallback to TLE computation
        if profile.get("altitude_km") is not None:
            orbital = {
                "altitude_km":      profile.get("altitude_km"),
                "apogee_km":        profile.get("apogee_km"),
                "perigee_km":       profile.get("perigee_km"),
                "orbit_type":       profile.get("orbit_type", "UNKNOWN"),
                "period_minutes":   profile.get("period_minutes"),
                "semi_major_axis":  profile.get("semi_major_axis"),
                "inclination":      profile.get("inclination"),
                "eccentricity":     profile.get("eccentricity"),
                "raan":             profile.get("raan"),
                "arg_of_perigee":   profile.get("arg_of_perigee"),
            }
        else:
            # Fall back to TLE-derived computation
            orbital = compute_all_orbital_elements(
                mean_motion=profile.get("mean_motion"),
                eccentricity=profile.get("eccentricity") or 0.0,
                inclination=profile.get("inclination"),
                raan=profile.get("raan"),
                arg_of_perigee=profile.get("arg_of_perigee"),
            )

        # Prefer stored risk; recalculate if missing
        if profile.get("risk_score") is not None:
            drivers_raw = profile.get("risk_drivers")
            try:
                drivers = json.loads(drivers_raw) if drivers_raw else []
            except (json.JSONDecodeError, TypeError):
                drivers = [drivers_raw] if drivers_raw else []
            risk = {
                "risk_score":     profile.get("risk_score"),
                "risk_level":     profile.get("risk_level"),
                "collision_risk": profile.get("collision_risk"),
                "debris_risk":    profile.get("debris_risk"),
                "altitude_risk":  profile.get("altitude_risk"),
                "risk_drivers":   drivers,
            }
        else:
            risk = calculate_risk(
                orbit_type=orbital.get("orbit_type", "UNKNOWN"),
                altitude_km=orbital.get("altitude_km"),
                inclination=orbital.get("inclination"),
                eccentricity=orbital.get("eccentricity"),
                debris_density=debris_density,
                conjunction_frequency=conjunction_frequency,
            )

    else:
        # ── Raw orbital params mode ──────────────────────────────────────────
        source = "raw_input"
        import math

        if altitude_km and not mean_motion:
            GM = 3.986004418e14
            a  = (altitude_km + 6371.0) * 1000
            T  = 2 * math.pi * math.sqrt(a**3 / GM)
            mean_motion = (24 * 3600) / T

        orbital = compute_all_orbital_elements(
            mean_motion=mean_motion,
            eccentricity=eccentricity or 0.0,
            inclination=inclination,
            raan=raan,
            arg_of_perigee=arg_of_perigee,
        )
        if altitude_km:
            orbital["altitude_km"] = altitude_km

        risk = calculate_risk(
            orbit_type=orbital.get("orbit_type", "UNKNOWN"),
            altitude_km=orbital.get("altitude_km"),
            inclination=inclination,
            eccentricity=eccentricity,
            debris_density=debris_density,
            conjunction_frequency=conjunction_frequency,
        )
        satellite = {"norad_id": None, "object_name": "Hypothetical Satellite"}

    # ── Step 2: Congestion data (neighbors) ──────────────────────────────────
    orbit_type  = orbital.get("orbit_type", "UNKNOWN")
    altitude    = orbital.get("altitude_km", 0) or 0

    neighbors        = get_orbit_neighbors(orbit_type, altitude, radius_km=100)
    high_risk_nearby = get_high_risk_neighbors(orbit_type, threshold=65.0)

    congestion = {
        "orbit_type":          orbit_type,
        "neighbor_count":      len(neighbors),
        "neighbors_sample":    neighbors[:5],          # top 5 by risk
        "high_risk_count":     len(high_risk_nearby),
        "high_risk_neighbors": high_risk_nearby,
    }

    # ── Step 3: Retrieve applicable regulatory context from Qdrant ────────────
    reg_query_data = {
        "orbit_type":   orbit_type,
        "altitude_km":  altitude,
        "risk_level":   risk.get("risk_level", "UNKNOWN"),
    }
    regulations = get_applicable_regulations(reg_query_data, top_k=4)

    # ── Step 4: Population-level context ─────────────────────────────────────
    population = get_population_metrics()

    return {
        "satellite":   satellite,
        "orbital":     orbital,
        "risk":        risk,
        "congestion":  congestion,
        "regulations": regulations,
        "population":  population,
        "source":      source,
        "error":       None,
    }
