from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from backend.services.satellite_service import SatelliteService

router = APIRouter()
service = SatelliteService()


# ── Request schema for raw orbital parameter input ────────────────────────────

class RawAnalysisRequest(BaseModel):
    mean_motion: Optional[float] = Field(None, description="TLE mean motion (rev/day)")
    eccentricity: Optional[float] = Field(None, ge=0, lt=1, description="Orbital eccentricity")
    inclination: Optional[float] = Field(None, ge=0, le=180, description="Inclination (degrees)")
    altitude_km: Optional[float] = Field(None, ge=0, description="Mean altitude (km) — alternative to mean_motion")
    raan: Optional[float] = Field(None, description="Right Ascension of Ascending Node (degrees)")
    arg_of_perigee: Optional[float] = Field(None, description="Argument of Perigee (degrees)")
    debris_density: Optional[float] = Field(None, ge=0, le=30, description="Local debris density override (0–30)")
    conjunction_frequency: Optional[float] = Field(None, ge=0, description="Conjunction events per week")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/{norad_id}", summary="Analyze satellite by NORAD ID")
def analyze_by_norad(
    norad_id: int,
    store: bool = Query(
        default=False,
        description="If true, persist computed results to orbital_parameters and risk_assessments tables"
    ),
):
    """
    Loads a satellite from the database by its NORAD Catalog ID and returns:
    - Computed orbital elements (altitude, apogee, perigee, period, orbit type)
    - Full risk profile (score, level, component scores, risk drivers)

    Set `?store=true` to persist the results back to the database.
    """
    if store:
        result = service.analyze_and_store(norad_id)
    else:
        result = service.analyze_satellite(norad_id=norad_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/raw", summary="Analyze from raw orbital parameters")
def analyze_raw(payload: RawAnalysisRequest):
    """
    Analyze a hypothetical or unlisted satellite using raw orbital parameters.
    Useful for:
    - What-if scenario analysis
    - Pre-launch mission assessment
    - Analyzing objects not yet in the database

    At least one of `mean_motion` or `altitude_km` must be provided.
    """
    if not payload.mean_motion and not payload.altitude_km:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of: mean_motion (rev/day) or altitude_km."
        )

    result = service.analyze_satellite(
        mean_motion=payload.mean_motion,
        altitude_km=payload.altitude_km,
        eccentricity=payload.eccentricity,
        inclination=payload.inclination,
        raan=payload.raan,
        arg_of_perigee=payload.arg_of_perigee,
        debris_density=payload.debris_density,
        conjunction_frequency=payload.conjunction_frequency,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/bulk", summary="Bulk analyze and store all unprocessed satellites")
def bulk_analyze(
    limit: int = Query(
        default=500, ge=1, le=5000,
        description="Max number of satellites to process in this call"
    )
):
    """
    Computes orbital parameters and risk scores for all satellites in the
    database that do not yet have computed results, and stores them.

    Run this once after loading CelesTrak data to populate the derived tables.
    """
    result = service.bulk_analyze_and_store(limit=limit)
    return result
