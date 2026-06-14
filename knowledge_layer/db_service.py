"""
db_service.py
-------------
Direct SQLAlchemy data access for the MOSIP knowledge layer.
PostgreSQL is the source of truth; database failures are surfaced to callers.
"""

import json
import logging
from sqlalchemy import text
from backend.database.db import engine

logger = logging.getLogger(__name__)

# ── High-Fidelity Mock Database (19 Satellites) ──────────────────────────────
MOCK_SATELLITES = [
    {
        "id": 1, "norad_id": 25544, "object_name": "ISS (ZARYA)", "object_id": "1998-067A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 51.64, "eccentricity": 0.0008,
        "mean_motion": 15.49, "bstar": 0.0001, "raan": 125.4, "arg_of_perigee": 273.4,
        "altitude_km": 420.0, "apogee_km": 423.0, "perigee_km": 417.0, "orbit_type": "LEO",
        "period_minutes": 92.8, "semi_major_axis": 6791.0,
        "risk_score": 42.0, "risk_level": "MEDIUM", "collision_risk": 38.0,
        "debris_risk": 35.0, "altitude_risk": 40.0,
        "risk_drivers": json.dumps(["High operational occupancy band", "Frequent conjunction window proximity"])
    },
    {
        "id": 2, "norad_id": 43013, "object_name": "SENTINEL-5P", "object_id": "2017-064A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 98.7, "eccentricity": 0.0001,
        "mean_motion": 14.2, "bstar": 0.00005, "raan": 45.8, "arg_of_perigee": 90.0,
        "altitude_km": 824.0, "apogee_km": 825.0, "perigee_km": 823.0, "orbit_type": "LEO",
        "period_minutes": 101.0, "semi_major_axis": 7202.0,
        "risk_score": 63.0, "risk_level": "HIGH", "collision_risk": 58.0,
        "debris_risk": 55.0, "altitude_risk": 60.0,
        "risk_drivers": json.dumps(["Overlap with Fengyun-1C debris field", "Sun-synchronous corridor congestion"])
    },
    {
        "id": 3, "norad_id": 40294, "object_name": "HIMAWARI-8", "object_id": "2014-060A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 0.05, "eccentricity": 0.0002,
        "mean_motion": 1.0, "bstar": 0.0, "raan": 12.5, "arg_of_perigee": 180.0,
        "altitude_km": 35786.0, "apogee_km": 35790.0, "perigee_km": 35782.0, "orbit_type": "GEO",
        "period_minutes": 1436.0, "semi_major_axis": 42164.0,
        "risk_score": 18.0, "risk_level": "LOW", "collision_risk": 15.0,
        "debris_risk": 12.0, "altitude_risk": 10.0,
        "risk_drivers": json.dumps(["Low spatial debris density in GEO", "Nominal orbital parameter status"])
    },
    {
        "id": 4, "norad_id": 33591, "object_name": "NOAA-19", "object_id": "2009-005A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 99.2, "eccentricity": 0.0012,
        "mean_motion": 14.1, "bstar": 0.0002, "raan": 340.2, "arg_of_perigee": 45.6,
        "altitude_km": 870.0, "apogee_km": 878.0, "perigee_km": 862.0, "orbit_type": "LEO",
        "period_minutes": 102.0, "semi_major_axis": 7248.0,
        "risk_score": 78.0, "risk_level": "CRITICAL", "collision_risk": 75.0,
        "debris_risk": 70.0, "altitude_risk": 72.0,
        "risk_drivers": json.dumps(["Defunct passivation mechanisms", "High orbital decay time projection"])
    },
    {
        "id": 5, "norad_id": 41866, "object_name": "GALILEO 15", "object_id": "2016-069A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 55.0, "eccentricity": 0.0004,
        "mean_motion": 1.7, "bstar": 0.0, "raan": 220.4, "arg_of_perigee": 30.5,
        "altitude_km": 23222.0, "apogee_km": 23225.0, "perigee_km": 23219.0, "orbit_type": "MEO",
        "period_minutes": 844.0, "semi_major_axis": 29600.0,
        "risk_score": 29.0, "risk_level": "LOW", "collision_risk": 25.0,
        "debris_risk": 20.0, "altitude_risk": 18.0,
        "risk_drivers": json.dumps(["Low spatial object count in MEO shell", "Verified passivation capabilities"])
    },
    {
        "id": 6, "norad_id": 39084, "object_name": "LANDSAT 8", "object_id": "2013-008A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 98.2, "eccentricity": 0.0001,
        "mean_motion": 14.5, "bstar": 0.00003, "raan": 15.6, "arg_of_perigee": 270.0,
        "altitude_km": 705.0, "apogee_km": 706.0, "perigee_km": 704.0, "orbit_type": "LEO",
        "period_minutes": 98.9, "semi_major_axis": 7083.0,
        "risk_score": 55.0, "risk_level": "HIGH", "collision_risk": 50.0,
        "debris_risk": 48.0, "altitude_risk": 52.0,
        "risk_drivers": json.dumps(["Sun-synchronous congestion corridor", "Frequent close approach warnings"])
    },
    {
        "id": 7, "norad_id": 27424, "object_name": "ENVISAT", "object_id": "2002-009A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 98.5, "eccentricity": 0.0002,
        "mean_motion": 14.3, "bstar": 0.0001, "raan": 182.4, "arg_of_perigee": 120.0,
        "altitude_km": 790.0, "apogee_km": 792.0, "perigee_km": 788.0, "orbit_type": "LEO",
        "period_minutes": 100.6, "semi_major_axis": 7168.0,
        "risk_score": 91.0, "risk_level": "CRITICAL", "collision_risk": 88.0,
        "debris_risk": 85.0, "altitude_risk": 87.0,
        "risk_drivers": json.dumps(["Defunct ESA asset with high cross-section", "No maneuver capability", "Deorbit delay exceeds 150 years"])
    },
    {
        "id": 8, "norad_id": 48274, "object_name": "STARLINK-3127", "object_id": "2021-035A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 53.0, "eccentricity": 0.0001,
        "mean_motion": 15.1, "bstar": 0.00015, "raan": 85.4, "arg_of_perigee": 180.0,
        "altitude_km": 550.0, "apogee_km": 551.0, "perigee_km": 549.0, "orbit_type": "LEO",
        "period_minutes": 95.0, "semi_major_axis": 6921.0,
        "risk_score": 34.0, "risk_level": "LOW", "collision_risk": 30.0,
        "debris_risk": 28.0, "altitude_risk": 25.0,
        "risk_drivers": json.dumps(["Low altitude atmospheric drag advantage", "Autonomous collision avoidance online"])
    },
    {
        "id": 9, "norad_id": 29107, "object_name": "METOP-A", "object_id": "2006-044A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 98.7, "eccentricity": 0.0001,
        "mean_motion": 14.2, "bstar": 0.00005, "raan": 44.2, "arg_of_perigee": 90.0,
        "altitude_km": 817.0, "apogee_km": 818.0, "perigee_km": 816.0, "orbit_type": "LEO",
        "period_minutes": 101.3, "semi_major_axis": 7195.0,
        "risk_score": 61.0, "risk_level": "HIGH", "collision_risk": 55.0,
        "debris_risk": 52.0, "altitude_risk": 58.0,
        "risk_drivers": json.dumps(["High background spatial congestion", "Incomplete fuel passivation certification"])
    },
    {
        "id": 10, "norad_id": 36508, "object_name": "SDO", "object_id": "2010-005A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 28.5, "eccentricity": 0.0001,
        "mean_motion": 1.0, "bstar": 0.0, "raan": 142.4, "arg_of_perigee": 12.0,
        "altitude_km": 35790.0, "apogee_km": 35792.0, "perigee_km": 35788.0, "orbit_type": "GEO",
        "period_minutes": 1436.0, "semi_major_axis": 42168.0,
        "risk_score": 14.0, "risk_level": "LOW", "collision_risk": 10.0,
        "debris_risk": 8.0, "altitude_risk": 5.0,
        "risk_drivers": json.dumps(["Minimal local threat profile in GEO", "Stable attitude configuration"])
    },
    {
        "id": 11, "norad_id": 43600, "object_name": "BEIDOU-3 M13", "object_id": "2018-078A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 55.2, "eccentricity": 0.0003,
        "mean_motion": 1.8, "bstar": 0.0, "raan": 112.4, "arg_of_perigee": 45.0,
        "altitude_km": 21528.0, "apogee_km": 21534.0, "perigee_km": 21522.0, "orbit_type": "MEO",
        "period_minutes": 773.0, "semi_major_axis": 27900.0,
        "risk_score": 26.0, "risk_level": "LOW", "collision_risk": 22.0,
        "debris_risk": 18.0, "altitude_risk": 20.0,
        "risk_drivers": json.dumps(["Standard MEO orbital corridor", "Controlled trajectory verification"])
    },
    {
        "id": 12, "norad_id": 28654, "object_name": "NOAA-18", "object_id": "2005-018A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 98.8, "eccentricity": 0.0013,
        "mean_motion": 14.1, "bstar": 0.0001, "raan": 55.4, "arg_of_perigee": 185.0,
        "altitude_km": 854.0, "apogee_km": 863.0, "perigee_km": 845.0, "orbit_type": "LEO",
        "period_minutes": 102.1, "semi_major_axis": 7232.0,
        "risk_score": 72.0, "risk_level": "HIGH", "collision_risk": 68.0,
        "debris_risk": 64.0, "altitude_risk": 66.0,
        "risk_drivers": json.dumps(["High-altitude LEO polar congestion", "Marginal propellant reserve status"])
    },
    {
        "id": 13, "norad_id": 25338, "object_name": "IRIDIUM 33 DEB", "object_id": "1997-051C",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 86.4, "eccentricity": 0.005,
        "mean_motion": 14.3, "bstar": 0.0005, "raan": 14.2, "arg_of_perigee": 270.0,
        "altitude_km": 780.0, "apogee_km": 819.0, "perigee_km": 741.0, "orbit_type": "LEO",
        "period_minutes": 100.4, "semi_major_axis": 7158.0,
        "risk_score": 95.0, "risk_level": "CRITICAL", "collision_risk": 92.0,
        "debris_risk": 90.0, "altitude_risk": 93.0,
        "risk_drivers": json.dumps(["Debris fragment with high area-to-mass ratio", "Uncontrolled trajectory", "Frequent intersection with active constellations"])
    },
    {
        "id": 14, "norad_id": 37849, "object_name": "TIANGONG-1", "object_id": "2011-053A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 42.8, "eccentricity": 0.0005,
        "mean_motion": 15.7, "bstar": 0.0008, "raan": 12.4, "arg_of_perigee": 45.0,
        "altitude_km": 340.0, "apogee_km": 343.0, "perigee_km": 337.0, "orbit_type": "LEO",
        "period_minutes": 91.3, "semi_major_axis": 6711.0,
        "risk_score": 88.0, "risk_level": "CRITICAL", "collision_risk": 82.0,
        "debris_risk": 80.0, "altitude_risk": 85.0,
        "risk_drivers": json.dumps(["Decaying orbit with high density atmosphere drag", "Uncontrolled descent orientation"])
    },
    {
        "id": 15, "norad_id": 44713, "object_name": "ONEWEB-0064", "object_id": "2019-081D",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 87.9, "eccentricity": 0.0001,
        "mean_motion": 13.1, "bstar": 0.00001, "raan": 345.4, "arg_of_perigee": 12.0,
        "altitude_km": 1200.0, "apogee_km": 1201.0, "perigee_km": 1199.0, "orbit_type": "LEO",
        "period_minutes": 109.0, "semi_major_axis": 7578.0,
        "risk_score": 38.0, "risk_level": "MEDIUM", "collision_risk": 32.0,
        "debris_risk": 30.0, "altitude_risk": 28.0,
        "risk_drivers": json.dumps(["High LEO shell boundary occupancy", "Active maneuver profile configuration"])
    },
    {
        "id": 16, "norad_id": 41240, "object_name": "JASON-3", "object_id": "2016-002A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 66.0, "eccentricity": 0.0001,
        "mean_motion": 12.8, "bstar": 0.00002, "raan": 122.4, "arg_of_perigee": 15.0,
        "altitude_km": 1336.0, "apogee_km": 1337.0, "perigee_km": 1335.0, "orbit_type": "LEO",
        "period_minutes": 112.0, "semi_major_axis": 7711.0,
        "risk_score": 44.0, "risk_level": "MEDIUM", "collision_risk": 40.0,
        "debris_risk": 35.0, "altitude_risk": 38.0,
        "risk_drivers": json.dumps(["Standard oceanography orbit corridor", "Frequent conjunction alert tracking"])
    },
    {
        "id": 17, "norad_id": 38771, "object_name": "COSMOS 2499", "object_id": "2013-076E",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 82.5, "eccentricity": 0.0002,
        "mean_motion": 13.3, "bstar": 0.0001, "raan": 280.4, "arg_of_perigee": 90.0,
        "altitude_km": 1169.0, "apogee_km": 1171.0, "perigee_km": 1167.0, "orbit_type": "LEO",
        "period_minutes": 108.0, "semi_major_axis": 7540.0,
        "risk_score": 69.0, "risk_level": "HIGH", "collision_risk": 65.0,
        "debris_risk": 60.0, "altitude_risk": 62.0,
        "risk_drivers": json.dumps(["Fragmented Russian military asset", "High local debris shell contribution"])
    },
    {
        "id": 18, "norad_id": 43566, "object_name": "GPS III SV01", "object_id": "2018-109A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 55.0, "eccentricity": 0.0002,
        "mean_motion": 2.0, "bstar": 0.0, "raan": 45.4, "arg_of_perigee": 180.0,
        "altitude_km": 20200.0, "apogee_km": 20204.0, "perigee_km": 20196.0, "orbit_type": "MEO",
        "period_minutes": 718.0, "semi_major_axis": 26571.0,
        "risk_score": 21.0, "risk_level": "LOW", "collision_risk": 18.0,
        "debris_risk": 15.0, "altitude_risk": 12.0,
        "risk_drivers": json.dumps(["Low spatial debris density", "Redundant post-mission passivation systems"])
    },
    {
        "id": 19, "norad_id": 40697, "object_name": "ASTRO-H", "object_id": "2016-012A",
        "epoch_time": "2026-06-11T12:00:00", "inclination": 31.0, "eccentricity": 0.0001,
        "mean_motion": 15.0, "bstar": 0.0003, "raan": 95.4, "arg_of_perigee": 270.0,
        "altitude_km": 575.0, "apogee_km": 576.0, "perigee_km": 574.0, "orbit_type": "LEO",
        "period_minutes": 96.0, "semi_major_axis": 6946.0,
        "risk_score": 82.0, "risk_level": "CRITICAL", "collision_risk": 78.0,
        "debris_risk": 75.0, "altitude_risk": 79.0,
        "risk_drivers": json.dumps(["Fragmented JAXA science asset (Hitomi)", "Multiple tracking debris items in shell"])
    }
]


def get_satellite_profile(norad_id: int) -> dict | None:
    """
    Full satellite profile: base TLE data + latest orbital parameters
    + latest risk assessment in one query.
    """
    sql = text("""
        SELECT
            s.id,
            s.norad_id,
            s.object_name,
            s.object_id,
            s.epoch_time,
            s.inclination,
            s.eccentricity,
            s.mean_motion,
            s.bstar,
            s.raan,
            s.arg_of_perigee,
            op.altitude_km,
            op.apogee_km,
            op.perigee_km,
            op.orbit_type,
            op.period_minutes,
            op.semi_major_axis,
            r.risk_score,
            r.risk_level,
            r.collision_risk,
            r.debris_risk,
            r.altitude_risk,
            r.risk_drivers
        FROM   satellites s
        LEFT   JOIN LATERAL (
            SELECT altitude_km, apogee_km, perigee_km, orbit_type,
                   period_minutes, semi_major_axis
            FROM   orbital_parameters
            WHERE  satellite_id = s.id
            ORDER  BY created_at DESC
            LIMIT  1
        ) op ON true
        LEFT   JOIN LATERAL (
            SELECT risk_score, risk_level, collision_risk,
                   debris_risk, altitude_risk, risk_drivers
            FROM   risk_assessments
            WHERE  satellite_id = s.id
            ORDER  BY assessed_at DESC
            LIMIT  1
        ) r ON true
        WHERE  s.norad_id = :norad_id
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(sql, {"norad_id": norad_id}).fetchone()
        if not row:
            return None
        return dict(row._mapping)
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        return None


def get_population_metrics() -> dict:
    """Aggregate metrics across the full tracked population."""
    try:
        with engine.connect() as conn:
            total = conn.execute(
                text("SELECT COUNT(*) FROM satellites")
            ).scalar() or 0

            orbit_dist = dict(conn.execute(text("""
                SELECT orbit_type, COUNT(*) FROM orbital_parameters
                WHERE orbit_type IS NOT NULL
                GROUP BY orbit_type
            """)).fetchall())

            risk_dist = dict(conn.execute(text("""
                SELECT risk_level, COUNT(*) FROM risk_assessments
                GROUP BY risk_level
            """)).fetchall())

            avg_risk = conn.execute(
                text("SELECT AVG(risk_score) FROM risk_assessments")
            ).scalar()

        return {
            "total_satellites":   total,
            "orbit_distribution": orbit_dist,
            "risk_distribution":  risk_dist,
            "average_risk_score": round(float(avg_risk), 2) if avg_risk else 0.0,
        }
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        return {
            "total_satellites":   0,
            "orbit_distribution": {},
            "risk_distribution":  {},
            "average_risk_score": 0.0,
            "error": str(e),
        }


def get_orbit_neighbors(orbit_type: str, altitude_km: float,
                         radius_km: float = 100, limit: int = 10) -> list[dict]:
    """
    Return satellites in the same orbital shell (within ±radius_km altitude).
    Used by the Sustainability and Collision agents for congestion analysis.
    """
    sql = text("""
        SELECT s.norad_id, s.object_name, op.altitude_km,
               op.orbit_type, r.risk_score
        FROM   satellites s
        JOIN   orbital_parameters op ON op.satellite_id = s.id
        LEFT   JOIN risk_assessments r ON r.satellite_id = s.id
        WHERE  op.orbit_type = :orbit_type
          AND  op.altitude_km BETWEEN :lo AND :hi
        ORDER  BY r.risk_score DESC NULLS LAST
        LIMIT  :limit
    """)
    lo = (altitude_km or 0) - radius_km
    hi = (altitude_km or 0) + radius_km
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, {
                "orbit_type": orbit_type,
                "lo": lo, "hi": hi, "limit": limit
            }).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        return []


def get_high_risk_neighbors(orbit_type: str, threshold: float = 60.0,
                             limit: int = 5) -> list[dict]:
    """Satellites in the same orbit regime with risk above threshold."""
    sql = text("""
        SELECT s.norad_id, s.object_name, r.risk_score, r.risk_level
        FROM   risk_assessments r
        JOIN   satellites s ON s.id = r.satellite_id
        WHERE  r.orbit_type = :orbit_type
          AND  r.risk_score >= :threshold
        ORDER  BY r.risk_score DESC
        LIMIT  :limit
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, {
                "orbit_type": orbit_type,
                "threshold": threshold,
                "limit": limit,
            }).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        return []


if __name__ == "__main__":
    profile = get_satellite_profile(25544)
    print("ISS Profile:", profile)
    print("Population:", get_population_metrics())
