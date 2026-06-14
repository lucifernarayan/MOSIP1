from sqlalchemy import text
from backend.database.db import engine


class SatelliteRepository:
    """Data-access layer for the satellites table and related joins."""

    # ── Basic CRUD ────────────────────────────────────────────────────────────

    def get_count(self) -> int:
        with engine.connect() as conn:
            return conn.execute(text("SELECT COUNT(*) FROM satellites")).scalar() or 0

    def get_all(self, limit: int = 100, offset: int = 0) -> list:
        sql = text("""
            SELECT id, norad_id, object_name, object_id, epoch_time,
                   inclination, eccentricity, mean_motion, bstar
            FROM   satellites
            ORDER  BY norad_id
            LIMIT  :limit OFFSET :offset
        """)
        with engine.connect() as conn:
            return conn.execute(sql, {"limit": limit, "offset": offset}).fetchall()

    def get_by_norad_id(self, norad_id: int) -> dict | None:
        sql = text("""
            SELECT s.id, s.norad_id, s.object_name, s.object_id, s.epoch_time,
                   s.inclination, s.eccentricity, s.mean_motion, s.bstar,
                   s.raan, s.arg_of_perigee
            FROM   satellites s
            WHERE  s.norad_id = :norad_id
        """)
        with engine.connect() as conn:
            row = conn.execute(sql, {"norad_id": norad_id}).fetchone()
        if not row:
            return None
        return dict(row._mapping)

    def get_by_name(self, name: str, limit: int = 20) -> list:
        sql = text("""
            SELECT s.norad_id, s.object_name, s.object_id, s.inclination, s.mean_motion,
                   op.altitude_km, op.orbit_type, r.risk_score, r.risk_level
            FROM   satellites
            s
            LEFT   JOIN LATERAL (
                SELECT altitude_km, orbit_type
                FROM   orbital_parameters
                WHERE  satellite_id = s.id
                ORDER  BY created_at DESC
                LIMIT  1
            ) op ON true
            LEFT   JOIN LATERAL (
                SELECT risk_score, risk_level
                FROM   risk_assessments
                WHERE  satellite_id = s.id
                ORDER  BY assessed_at DESC
                LIMIT  1
            ) r ON true
            WHERE  UPPER(s.object_name) LIKE UPPER(:pattern)
               OR  CAST(s.norad_id AS TEXT) LIKE :pattern
            ORDER  BY s.object_name
            LIMIT  :limit
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"pattern": f"%{name}%", "limit": limit}).fetchall()
        return [dict(row._mapping) for row in rows]

    # ── Rich joined queries ───────────────────────────────────────────────────

    def get_full_profile(self, norad_id: int) -> dict | None:
        """
        Returns satellite + latest orbital parameters + latest risk assessment.
        """
        sql = text("""
            SELECT
                s.norad_id,
                s.object_name,
                s.object_id,
                s.epoch_time,
                op.altitude_km,
                op.apogee_km,
                op.perigee_km,
                op.orbit_type,
                op.period_minutes,
                op.inclination,
                op.eccentricity,
                op.raan,
                op.arg_of_perigee,
                r.risk_score,
                r.risk_level,
                r.collision_risk,
                r.debris_risk,
                r.altitude_risk,
                r.risk_drivers
            FROM   satellites s
            LEFT   JOIN orbital_parameters op ON op.satellite_id = s.id
            LEFT   JOIN risk_assessments   r  ON r.satellite_id  = s.id
            WHERE  s.norad_id = :norad_id
            ORDER  BY op.created_at DESC, r.assessed_at DESC
            LIMIT  1
        """)
        with engine.connect() as conn:
            row = conn.execute(sql, {"norad_id": norad_id}).fetchone()
        if not row:
            return None
        return dict(row._mapping)

    def get_satellites_with_risk(self, limit: int = 100, offset: int = 0) -> list:
        """Paginated list with joined orbital + risk data for the API /satellites endpoint."""
        sql = text("""
            SELECT
                s.norad_id,
                s.object_name,
                op.altitude_km,
                op.orbit_type,
                r.risk_score,
                r.risk_level
            FROM   satellites s
            LEFT   JOIN LATERAL (
                SELECT altitude_km, orbit_type
                FROM   orbital_parameters
                WHERE  satellite_id = s.id
                ORDER  BY created_at DESC
                LIMIT  1
            ) op ON true
            LEFT   JOIN LATERAL (
                SELECT risk_score, risk_level
                FROM   risk_assessments
                WHERE  satellite_id = s.id
                ORDER  BY assessed_at DESC
                LIMIT  1
            ) r ON true
            ORDER  BY s.norad_id
            LIMIT  :limit OFFSET :offset
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"limit": limit, "offset": offset}).fetchall()
        return [dict(row._mapping) for row in rows]

    def get_by_orbit_type(self, orbit_type: str, limit: int = 100) -> list:
        sql = text("""
            SELECT s.norad_id, s.object_name, op.altitude_km,
                   op.inclination, r.risk_score, r.risk_level
            FROM   satellites s
            JOIN   orbital_parameters op ON op.satellite_id = s.id
            LEFT   JOIN risk_assessments r ON r.satellite_id = s.id
            WHERE  op.orbit_type = :orbit_type
            ORDER  BY r.risk_score DESC NULLS LAST
            LIMIT  :limit
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"orbit_type": orbit_type.upper(), "limit": limit}).fetchall()
        return [dict(row._mapping) for row in rows]

    def get_high_risk(self, threshold: float = 50.0, limit: int = 50) -> list:
        sql = text("""
            SELECT s.norad_id, s.object_name, r.risk_score, r.risk_level,
                   r.orbit_type, r.risk_drivers
            FROM   risk_assessments r
            JOIN   satellites s ON s.id = r.satellite_id
            WHERE  r.risk_score >= :threshold
            ORDER  BY r.risk_score DESC
            LIMIT  :limit
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"threshold": threshold, "limit": limit}).fetchall()
        return [dict(row._mapping) for row in rows]
