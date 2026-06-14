import json
from sqlalchemy import text
from backend.database.db import engine
from backend.risk.orbit_classifier import compute_all_orbital_elements
from backend.risk.risk_engine import calculate_risk
from backend.repositories.satellite_repository import SatelliteRepository


repo = SatelliteRepository()


class SatelliteService:
    """
    Business logic layer.
    Orchestrates orbit computation + risk scoring + DB persistence.
    """

    def analyze_satellite(
        self,
        norad_id: int = None,
        altitude_km: float = None,
        mean_motion: float = None,
        eccentricity: float = None,
        inclination: float = None,
        raan: float = None,
        arg_of_perigee: float = None,
        debris_density: float = None,
        conjunction_frequency: float = None,
    ) -> dict:
        """
        Compute orbital elements + risk profile for a satellite.

        If norad_id is given → loads from DB.
        If raw orbital params given → computes on-the-fly (no DB write).
        """
        # ── Load from DB if norad_id provided ────────────────────────────────
        if norad_id is not None:
            sat = repo.get_by_norad_id(norad_id)
            if not sat:
                return {"error": f"Satellite NORAD {norad_id} not found in database."}

            mean_motion = sat.get("mean_motion") or mean_motion
            eccentricity = sat.get("eccentricity") or eccentricity
            inclination = sat.get("inclination") or inclination
            raan = sat.get("raan") or raan
            arg_of_perigee = sat.get("arg_of_perigee") or arg_of_perigee
            object_name = sat.get("object_name")
        else:
            object_name = "Unknown"

        # ── If altitude given directly, derive mean_motion estimate ───────────
        # (for manual input where mean_motion isn't available)
        if altitude_km and not mean_motion:
            # Approximate mean_motion from altitude using Kepler
            import math
            GM = 3.986004418e14
            a = (altitude_km + 6371.0) * 1000  # metres
            T = 2 * math.pi * math.sqrt(a**3 / GM)
            mean_motion = (24 * 3600) / T

        # ── Orbital elements ──────────────────────────────────────────────────
        orbital = compute_all_orbital_elements(
            mean_motion=mean_motion,
            eccentricity=eccentricity or 0.0,
            inclination=inclination,
            raan=raan,
            arg_of_perigee=arg_of_perigee,
        )

        # ── Risk scoring ──────────────────────────────────────────────────────
        risk = calculate_risk(
            orbit_type=orbital["orbit_type"],
            altitude_km=orbital["altitude_km"],
            inclination=inclination,
            eccentricity=eccentricity,
            debris_density=debris_density,
            conjunction_frequency=conjunction_frequency,
        )

        return {
            "norad_id": norad_id,
            "object_name": object_name,
            "orbital": orbital,
            "risk": risk,
        }

    def analyze_and_store(self, norad_id: int) -> dict:
        """
        Analyze a satellite from the DB and persist the results back
        into orbital_parameters and risk_assessments tables.
        """
        result = self.analyze_satellite(norad_id=norad_id)
        if "error" in result:
            return result

        sat = repo.get_by_norad_id(norad_id)
        satellite_id = sat["id"]
        orbital = result["orbital"]
        risk = result["risk"]

        with engine.begin() as conn:
            # Upsert orbital_parameters
            conn.execute(text("""
                INSERT INTO orbital_parameters (
                    satellite_id, epoch_time, inclination, eccentricity,
                    mean_motion, altitude_km, apogee_km, perigee_km,
                    semi_major_axis, raan, arg_of_perigee,
                    period_minutes, orbit_type
                )
                VALUES (
                    :satellite_id, NOW(), :inclination, :eccentricity,
                    :mean_motion, :altitude_km, :apogee_km, :perigee_km,
                    :semi_major_axis, :raan, :arg_of_perigee,
                    :period_minutes, :orbit_type
                )
                ON CONFLICT DO NOTHING
            """), {
                "satellite_id":   satellite_id,
                "inclination":    orbital["inclination"],
                "eccentricity":   orbital["eccentricity"],
                "mean_motion":    sat.get("mean_motion"),
                "altitude_km":    orbital["altitude_km"],
                "apogee_km":      orbital["apogee_km"],
                "perigee_km":     orbital["perigee_km"],
                "semi_major_axis": orbital["semi_major_axis_km"],
                "raan":           orbital["raan"],
                "arg_of_perigee": orbital["arg_of_perigee"],
                "period_minutes": orbital["period_minutes"],
                "orbit_type":     orbital["orbit_type"],
            })

            # Upsert risk_assessments
            conn.execute(text("""
                INSERT INTO risk_assessments (
                    satellite_id, risk_score, risk_level,
                    collision_risk, debris_risk, altitude_risk,
                    orbit_type, risk_drivers
                )
                VALUES (
                    :satellite_id, :risk_score, :risk_level,
                    :collision_risk, :debris_risk, :altitude_risk,
                    :orbit_type, :risk_drivers
                )
                ON CONFLICT DO NOTHING
            """), {
                "satellite_id":   satellite_id,
                "risk_score":     risk["risk_score"],
                "risk_level":     risk["risk_level"],
                "collision_risk": risk["collision_risk"],
                "debris_risk":    risk["debris_risk"],
                "altitude_risk":  risk["altitude_risk"],
                "orbit_type":     orbital["orbit_type"],
                "risk_drivers":   json.dumps(risk["risk_drivers"]),
            })

        result["stored"] = True
        return result

    def bulk_analyze_and_store(self, limit: int = 500) -> dict:
        """
        Process up to `limit` satellites from the DB — compute and store
        orbital parameters + risk assessments in bulk.
        Useful for the initial data load.
        """
        sql = text("""
            SELECT norad_id FROM satellites
            WHERE norad_id NOT IN (
                SELECT s.norad_id FROM satellites s
                JOIN orbital_parameters op ON op.satellite_id = s.id
            )
            LIMIT :limit
        """)
        with engine.connect() as conn:
            norad_ids = [row[0] for row in conn.execute(sql, {"limit": limit}).fetchall()]

        success = 0
        errors = 0
        for nid in norad_ids:
            result = self.analyze_and_store(nid)
            if "error" in result:
                errors += 1
            else:
                success += 1

        return {
            "processed": len(norad_ids),
            "success": success,
            "errors": errors,
        }