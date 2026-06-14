from fastapi import APIRouter, Query
from backend.analytics.orbital_metrics import OrbitalMetrics

router = APIRouter()
metrics = OrbitalMetrics()


@router.get("/summary", summary="Full population summary")
def population_summary():
    """
    Returns a complete overview of the tracked orbital population:
    - Total satellite count
    - Distribution by orbit type (LEO, MEO, GEO, HEO, VLEO)
    - Risk level distribution (LOW, MEDIUM, HIGH, CRITICAL)
    - Average risk score
    - Altitude statistics (min, max, average)
    """
    return metrics.population_summary()


@router.get("/orbits", summary="Satellite count by orbital regime")
def orbit_distribution():
    """Returns how many satellites are tracked in each orbital regime."""
    return {
        "VLEO": metrics.count_vleo(),
        "LEO":  metrics.count_leo(),
        "MEO":  metrics.count_meo(),
        "GEO":  metrics.count_geo(),
        "HEO":  metrics.count_heo(),
    }


@router.get("/risk", summary="Risk distribution across population")
def risk_distribution():
    """Returns the count of satellites in each risk category."""
    return {
        "distribution": metrics.risk_distribution(),
        "average_score": metrics.average_risk_score(),
        "critical_count": metrics.critical_risk_count(),
    }


@router.get("/risk/top", summary="Top N highest-risk satellites")
def top_risk_satellites(
    limit: int = Query(default=20, ge=1, le=100, description="Number of satellites to return")
):
    """Returns the N satellites with the highest computed risk scores."""
    return {
        "count": limit,
        "satellites": metrics.high_risk_satellites(limit=limit),
    }


@router.get("/altitude", summary="Altitude statistics")
def altitude_stats():
    """Returns min, max, and average altitude across all tracked satellites."""
    return metrics.altitude_stats()


@router.get("/altitude/histogram", summary="Altitude distribution histogram (LEO focus)")
def altitude_histogram(
    bins: int = Query(default=10, ge=2, le=50, description="Number of histogram bins (0–2000 km)")
):
    """
    Returns a histogram of satellite count vs altitude for the 0–2000 km range
    (LEO and VLEO). Useful for visualising orbital shell congestion.
    """
    return {
        "range_km": "0–2000",
        "bins": bins,
        "histogram": metrics.altitude_histogram(bins=bins),
    }
