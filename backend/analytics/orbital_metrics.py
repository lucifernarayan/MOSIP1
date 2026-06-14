from sqlalchemy import text
from backend.database.db import engine


class OrbitalMetrics:
    """
    Aggregate analytics over the full satellite population in the DB.
    All methods query live data — no caching.
    """

    # ── Orbit-type counts ─────────────────────────────────────────────────────

    def count_by_orbit(self) -> dict:
        """Return count of satellites in each orbital regime."""
        sql = text("""
            SELECT orbit_type, COUNT(*) AS cnt
            FROM   orbital_parameters
            WHERE  orbit_type IS NOT NULL
            GROUP  BY orbit_type
            ORDER  BY cnt DESC
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql).fetchall()
        return {row[0]: row[1] for row in rows}

    def count_leo(self) -> int:
        sql = text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type = 'LEO'")
        with engine.connect() as conn:
            return conn.execute(sql).scalar() or 0

    def count_vleo(self) -> int:
        sql = text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type = 'VLEO'")
        with engine.connect() as conn:
            return conn.execute(sql).scalar() or 0

    def count_meo(self) -> int:
        sql = text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type = 'MEO'")
        with engine.connect() as conn:
            return conn.execute(sql).scalar() or 0

    def count_geo(self) -> int:
        sql = text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type = 'GEO'")
        with engine.connect() as conn:
            return conn.execute(sql).scalar() or 0

    def count_heo(self) -> int:
        sql = text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type = 'HEO'")
        with engine.connect() as conn:
            return conn.execute(sql).scalar() or 0

    # ── Risk analytics ────────────────────────────────────────────────────────

    def average_risk_score(self) -> float:
        sql = text("SELECT AVG(risk_score) FROM risk_assessments")
        with engine.connect() as conn:
            result = conn.execute(sql).scalar()
        return round(float(result), 2) if result else 0.0

    def risk_distribution(self) -> dict:
        """Count of satellites per risk level."""
        sql = text("""
            SELECT risk_level, COUNT(*) AS cnt
            FROM   risk_assessments
            GROUP  BY risk_level
            ORDER  BY cnt DESC
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql).fetchall()
        return {row[0]: row[1] for row in rows}

    def high_risk_satellites(self, limit: int = 20) -> list:
        """
        Return top N highest-risk satellites with their names and scores.
        """
        sql = text("""
            SELECT
                s.norad_id,
                s.object_name,
                r.risk_score,
                r.risk_level,
                r.orbit_type,
                r.risk_drivers
            FROM   risk_assessments r
            JOIN   satellites       s ON s.id = r.satellite_id
            ORDER  BY r.risk_score DESC
            LIMIT  :limit
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"limit": limit}).fetchall()
        return [
            {
                "norad_id":    row[0],
                "object_name": row[1],
                "risk_score":  row[2],
                "risk_level":  row[3],
                "orbit_type":  row[4],
                "risk_drivers": row[5],
            }
            for row in rows
        ]

    def critical_risk_count(self) -> int:
        sql = text("SELECT COUNT(*) FROM risk_assessments WHERE risk_level = 'CRITICAL'")
        with engine.connect() as conn:
            return conn.execute(sql).scalar() or 0

    # ── Altitude analytics ────────────────────────────────────────────────────

    def altitude_stats(self) -> dict:
        """Min, max, average altitude across the tracked population."""
        sql = text("""
            SELECT
                MIN(altitude_km)  AS min_alt,
                MAX(altitude_km)  AS max_alt,
                AVG(altitude_km)  AS avg_alt
            FROM orbital_parameters
            WHERE altitude_km IS NOT NULL AND altitude_km > 0
        """)
        with engine.connect() as conn:
            row = conn.execute(sql).fetchone()
        if not row or row[0] is None:
            return {"min_km": None, "max_km": None, "avg_km": None}
        return {
            "min_km": round(row[0], 1),
            "max_km": round(row[1], 1),
            "avg_km": round(row[2], 1),
        }

    def altitude_histogram(self, bins: int = 10) -> list:
        """
        Returns altitude distribution across equal-width bins (0–2000 km for LEO focus).
        Each bucket: { range: "300–500 km", count: N }
        """
        sql = text("""
            SELECT
                width_bucket(altitude_km, 0, 2000, :bins) AS bucket,
                COUNT(*) AS cnt
            FROM   orbital_parameters
            WHERE  altitude_km BETWEEN 0 AND 2000
            GROUP  BY bucket
            ORDER  BY bucket
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"bins": bins}).fetchall()
        bucket_width = 2000 // bins
        return [
            {
                "range": f"{(row[0] - 1) * bucket_width}–{row[0] * bucket_width} km",
                "count": row[1],
            }
            for row in rows
            if row[0] is not None
        ]

    # ── Population summary ────────────────────────────────────────────────────

    def population_summary(self) -> dict:
        """Single call that returns a complete population overview."""
        total_sql = text("SELECT COUNT(*) FROM satellites")
        with engine.connect() as conn:
            total = conn.execute(total_sql).scalar() or 0

        return {
            "total_satellites": total,
            "orbit_distribution": self.count_by_orbit(),
            "risk_distribution": self.risk_distribution(),
            "average_risk_score": self.average_risk_score(),
            "critical_risk_count": self.critical_risk_count(),
            "altitude_stats": self.altitude_stats(),
        }