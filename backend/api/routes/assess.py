"""
assess.py
---------
MOSIP Intelligence Assessment API Routes.

Exposes the full multi-agent LangGraph pipeline via REST endpoints.

Endpoints:
  GET  /assess/{norad_id}             → Full 8-agent assessment
  POST /assess/raw                    → Assessment from raw orbital params
  GET  /assess/{norad_id}/orbital     → Orbital agent only
  GET  /assess/{norad_id}/collision   → Collision risk agent only
  GET  /assess/{norad_id}/compliance  → Compliance agent only
  GET  /assess/{norad_id}/forecast    → Forecast agent only
  GET  /assess/{norad_id}/mitigation  → Mitigation agent only
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from knowledge_layer.orchestrator import run_full_assessment, run_agent_only

router = APIRouter()


# ── Request schema for raw orbital params ─────────────────────────────────────

class RawAssessmentRequest(BaseModel):
    altitude_km:           Optional[float] = Field(None, ge=0, description="Mean altitude (km)")
    mean_motion:           Optional[float] = Field(None, description="TLE mean motion (rev/day)")
    eccentricity:          Optional[float] = Field(None, ge=0, lt=1)
    inclination:           Optional[float] = Field(None, ge=0, le=180)
    raan:                  Optional[float] = Field(None, description="Right Ascension of Ascending Node (deg)")
    arg_of_perigee:        Optional[float] = Field(None)
    debris_density:        Optional[float] = Field(None, ge=0, le=30)
    conjunction_frequency: Optional[float] = Field(None, ge=0)


# ── Helper: format the final assessment response ──────────────────────────────

def _format_assessment(state: dict) -> dict:
    """
    Format the full MOSIPState into a clean API response.
    Strips internal fields and structures output for the frontend.
    """
    errors = state.get("errors", [])

    return {
        "satellite":             state.get("satellite_data", {}),
        "orbital_analysis":      state.get("orbital_analysis", {}),
        "collision_analysis":    state.get("collision_analysis", {}),
        "compliance_analysis":   state.get("compliance_analysis", {}),
        "sustainability_analysis": state.get("sustainability_analysis", {}),
        "forecast":              state.get("forecast", {}),
        "mitigation_analysis":   state.get("mitigation_analysis", {}),
        "recommendations":       state.get("recommendations", []),
        "report":                state.get("report", ""),
        "agent_timeline":        state.get("agent_timeline", []),
        "regulations":           state.get("regulations", []),
        "regulations_used":      len(state.get("regulations", [])),
        "errors":                errors,
        "status":                "error" if errors else "complete",
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/{norad_id}",
    summary="Full MOSIP multi-agent intelligence assessment",
    description=(
        "Runs the complete 8-agent MOSIP pipeline for a satellite by NORAD ID. "
        "Returns risk, compliance, sustainability, forecast, mitigation intelligence, "
        "and a full executive report. ⚠️ This call takes 10-30 seconds (LLM reasoning)."
    ),
)
def full_assessment(norad_id: int):
    """Full multi-agent intelligence assessment for a satellite."""
    state = run_full_assessment(norad_id=norad_id)

    if state.get("errors") and not state.get("satellite_data"):
        raise HTTPException(
            status_code=404,
            detail=state["errors"][0] if state["errors"] else "Assessment failed.",
        )

    return _format_assessment(state)


@router.post(
    "/raw",
    summary="Full MOSIP assessment from raw orbital parameters",
    description=(
        "Analyze a hypothetical or unlisted satellite using raw orbital parameters. "
        "Useful for pre-launch assessments, what-if scenarios, or unlisted objects."
    ),
)
def raw_assessment(payload: RawAssessmentRequest):
    """Full assessment from raw orbital parameters (no NORAD ID required)."""
    if not payload.altitude_km and not payload.mean_motion:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of: altitude_km or mean_motion.",
        )

    raw_params = payload.model_dump(exclude_none=True)
    state = run_full_assessment(raw_params=raw_params)

    return _format_assessment(state)


# ── Single-agent endpoints (faster, no full pipeline) ────────────────────────

@router.get(
    "/{norad_id}/orbital",
    summary="Orbital analysis only",
    description="Runs only the Orbital Analysis Agent (fast, no LLM).",
)
def orbital_only(norad_id: int):
    return run_agent_only("orbital", norad_id=norad_id)


@router.get(
    "/{norad_id}/collision",
    summary="Collision risk analysis only",
    description="Runs Orbital + Collision Risk agents (fast, no LLM).",
)
def collision_only(norad_id: int):
    return run_agent_only("collision", norad_id=norad_id)


@router.get(
    "/{norad_id}/compliance",
    summary="Compliance assessment only (LLM + Qdrant RAG)",
    description=(
        "Runs the Compliance Agent with Qdrant regulatory retrieval and LLM grading. "
        "Checks against ESA, IADC, and NASA disposal guidelines."
    ),
)
def compliance_only(norad_id: int):
    return run_agent_only("compliance", norad_id=norad_id)


@router.get(
    "/{norad_id}/sustainability",
    summary="Sustainability assessment only",
    description="Runs Sustainability Agent — orbital burden, footprint, and ecosystem impact.",
)
def sustainability_only(norad_id: int):
    return run_agent_only("sustainability", norad_id=norad_id)


@router.get(
    "/{norad_id}/forecast",
    summary="Forecast assessment only",
    description="Runs Forecast Agent — 5/10/25-year debris and collision probability projections.",
)
def forecast_only(norad_id: int):
    return run_agent_only("forecast", norad_id=norad_id)


@router.get(
    "/{norad_id}/mitigation",
    summary="Mitigation recommendations only",
    description="Runs full pipeline up to Mitigation Agent for actionable recommendations.",
)
def mitigation_only(norad_id: int):
    return run_agent_only("mitigation", norad_id=norad_id)
