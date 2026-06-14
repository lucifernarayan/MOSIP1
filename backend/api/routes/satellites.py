from fastapi import APIRouter, HTTPException, Query
from backend.repositories.satellite_repository import SatelliteRepository

router = APIRouter()
repo = SatelliteRepository()


@router.get("/", summary="List all satellites (paginated)")
def list_satellites(
    limit: int  = Query(default=50, ge=1, le=500, description="Results per page"),
    offset: int = Query(default=0,  ge=0,          description="Pagination offset"),
    orbit: str  = Query(default=None,               description="Filter by orbit type: LEO, MEO, GEO, HEO, VLEO"),
):
    """
    Returns a paginated list of tracked satellites with their orbital regime
    and risk score. Use `orbit` to filter by regime.
    """
    if orbit:
        data = repo.get_by_orbit_type(orbit.upper(), limit=limit)
    else:
        data = repo.get_satellites_with_risk(limit=limit, offset=offset)

    return {
        "total_returned": len(data),
        "limit": limit,
        "offset": offset,
        "orbit_filter": orbit,
        "satellites": data,
    }


@router.get("/count", summary="Total satellite count")
def satellite_count():
    """Returns total number of satellites in the database."""
    return {"total": repo.get_count()}


@router.get("/search", summary="Search satellites by name")
def search_satellites(
    q: str = Query(..., min_length=2, description="Name fragment to search"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Search for satellites by partial name match (case-insensitive)."""
    results = repo.get_by_name(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@router.get("/high-risk", summary="Highest risk satellites")
def high_risk_satellites(
    threshold: float = Query(default=50.0, ge=0, le=100, description="Minimum risk score"),
    limit: int = Query(default=25, ge=1, le=100),
):
    """Returns satellites with a risk score above the given threshold."""
    results = repo.get_high_risk(threshold=threshold, limit=limit)
    return {
        "threshold": threshold,
        "count": len(results),
        "satellites": results,
    }


@router.get("/{norad_id}", summary="Full satellite profile")
def satellite_profile(norad_id: int):
    """
    Returns the complete profile of a satellite by NORAD Catalog ID,
    including orbital parameters and risk assessment.
    """
    profile = repo.get_full_profile(norad_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Satellite with NORAD ID {norad_id} not found."
        )
    return profile
