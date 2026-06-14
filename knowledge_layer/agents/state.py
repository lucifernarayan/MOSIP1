"""
state.py
--------
Shared LangGraph state for the MOSIP multi-agent pipeline.

Every agent reads from and writes to this TypedDict.
The Supervisor orchestrates routing and reads the final state.
"""

from typing import TypedDict, Optional, Any


class MOSIPState(TypedDict):
    """
    Single shared state passed through the entire LangGraph pipeline.
    Agents only update their own keys — they do not overwrite others.
    """

    # ── Input ─────────────────────────────────────────────────────────────────
    norad_id:             Optional[int]
    raw_params:           dict           # raw orbital params for hypothetical analysis

    # ── Phase 1: Unified intelligence context (set by gather step) ───────────
    satellite_data:       dict           # identity: name, norad_id, epoch
    orbital_data:         dict           # altitude, orbit_type, apogee, perigee, ...
    risk_data:            dict           # risk_score, risk_level, components, drivers
    congestion_data:      dict           # neighbors, high_risk_nearby
    population_data:      dict           # total satellites, orbit/risk distributions
    regulations:          list[dict]     # Qdrant-retrieved regulatory chunks

    # ── Agent outputs ─────────────────────────────────────────────────────────
    orbital_analysis:     dict           # Orbital Agent output
    collision_analysis:   dict           # Collision Risk Agent output
    compliance_analysis:  dict           # Compliance Agent output (LLM + Qdrant)
    sustainability_analysis: dict        # Sustainability Agent output
    forecast:             dict           # Forecast Agent output
    recommendations:      list[str]      # Mitigation Agent output
    mitigation_analysis:  dict           # Full mitigation dict
    report:               str            # Documentation Agent — final executive report

    # ── Meta ──────────────────────────────────────────────────────────────────
    agent_timeline:       list[dict]     # [{agent, status, timestamp, summary}, ...]
    errors:               list[str]      # non-fatal errors collected during run
