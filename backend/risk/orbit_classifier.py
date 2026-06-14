import math

# Physical constants
GM_EARTH = 3.986004418e14   # Earth's gravitational parameter (m^3/s^2)
R_EARTH_KM = 6371.0         # Earth's mean radius (km)


def mean_motion_to_altitude(mean_motion_rev_per_day: float) -> dict:
    """
    Convert TLE mean motion (rev/day) to orbital elements.

    Uses Kepler's Third Law:
        T = 1 / n   (period in days)
        a^3 = GM * T^2 / (4 * pi^2)

    Returns a dict with semi_major_axis, altitude_km, period_minutes.
    """
    if not mean_motion_rev_per_day or mean_motion_rev_per_day <= 0:
        return {
            "semi_major_axis_km": None,
            "altitude_km": None,
            "period_minutes": None,
        }

    # Period in seconds
    period_s = (24 * 3600) / mean_motion_rev_per_day

    # Semi-major axis in meters (Kepler's Third Law)
    a_m = (GM_EARTH * (period_s / (2 * math.pi)) ** 2) ** (1 / 3)
    a_km = a_m / 1000.0

    altitude_km = a_km - R_EARTH_KM
    period_min = period_s / 60.0

    return {
        "semi_major_axis_km": round(a_km, 3),
        "altitude_km": round(altitude_km, 3),
        "period_minutes": round(period_min, 3),
    }


def compute_apogee_perigee(semi_major_axis_km: float, eccentricity: float) -> dict:
    """
    Compute apogee and perigee altitudes from semi-major axis and eccentricity.

    apogee_radius  = a * (1 + e)
    perigee_radius = a * (1 - e)
    altitude       = radius - R_earth
    """
    if semi_major_axis_km is None or eccentricity is None:
        return {"apogee_km": None, "perigee_km": None}

    apogee_km  = semi_major_axis_km * (1 + eccentricity) - R_EARTH_KM
    perigee_km = semi_major_axis_km * (1 - eccentricity) - R_EARTH_KM

    return {
        "apogee_km": round(apogee_km, 3),
        "perigee_km": round(perigee_km, 3),
    }


def classify_orbit(altitude_km: float) -> str:
    """
    Classify orbital regime from mean altitude.

    VLEO  : < 300 km   (very low, decays quickly)
    LEO   : 300–2000 km
    MEO   : 2000–35786 km
    GEO   : 35786 ± 200 km
    HEO   : highly eccentric / other
    """
    if altitude_km is None:
        return "UNKNOWN"
    if altitude_km < 300:
        return "VLEO"
    elif altitude_km < 2000:
        return "LEO"
    elif altitude_km < 35586:
        return "MEO"
    elif altitude_km <= 35986:
        return "GEO"
    else:
        return "HEO"


def compute_all_orbital_elements(
    mean_motion: float,
    eccentricity: float,
    inclination: float,
    raan: float = None,
    arg_of_perigee: float = None,
) -> dict:
    """
    Master function — compute all derived orbital elements from raw TLE values.
    Returns a complete orbital profile dictionary.
    """
    basics = mean_motion_to_altitude(mean_motion)
    a_km = basics["semi_major_axis_km"]
    altitude_km = basics["altitude_km"]

    ap = compute_apogee_perigee(a_km, eccentricity or 0.0)
    orbit_type = classify_orbit(altitude_km)

    return {
        "semi_major_axis_km": a_km,
        "altitude_km": altitude_km,
        "apogee_km": ap["apogee_km"],
        "perigee_km": ap["perigee_km"],
        "period_minutes": basics["period_minutes"],
        "orbit_type": orbit_type,
        "inclination": inclination,
        "eccentricity": eccentricity,
        "raan": raan,
        "arg_of_perigee": arg_of_perigee,
    }