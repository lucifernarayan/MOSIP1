-- ============================================================
-- MOSIP Database Schema
-- ============================================================

-- Satellites: core identity of each space object
CREATE TABLE IF NOT EXISTS satellites (
    id              SERIAL PRIMARY KEY,
    norad_id        INTEGER UNIQUE NOT NULL,
    object_name     VARCHAR(255),
    object_id       VARCHAR(100),
    epoch_time      TIMESTAMP,
    inclination     FLOAT,
    eccentricity    FLOAT,
    mean_motion     FLOAT,          -- revolutions per day
    bstar           FLOAT,          -- drag coefficient
    raan            FLOAT,          -- right ascension of ascending node (deg)
    arg_of_perigee  FLOAT,          -- argument of perigee (deg)
    mean_anomaly    FLOAT,          -- mean anomaly (deg)
    rev_at_epoch    INTEGER,        -- revolution number at epoch
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orbital Parameters: computed/derived orbital elements per satellite
CREATE TABLE IF NOT EXISTS orbital_parameters (
    id              SERIAL PRIMARY KEY,
    satellite_id    INTEGER NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    epoch_time      TIMESTAMP,
    inclination     FLOAT,          -- degrees
    eccentricity    FLOAT,
    mean_motion     FLOAT,          -- rev/day
    altitude_km     FLOAT,          -- computed mean altitude (km)
    apogee_km       FLOAT,          -- apogee altitude (km)
    perigee_km      FLOAT,          -- perigee altitude (km)
    semi_major_axis FLOAT,          -- km
    raan            FLOAT,          -- degrees
    arg_of_perigee  FLOAT,          -- degrees
    period_minutes  FLOAT,          -- orbital period in minutes
    orbit_type      VARCHAR(10),    -- LEO / MEO / GEO / HEO / VLEO
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk Assessments: computed risk profile per satellite
CREATE TABLE IF NOT EXISTS risk_assessments (
    id                  SERIAL PRIMARY KEY,
    satellite_id        INTEGER NOT NULL REFERENCES satellites(id) ON DELETE CASCADE,
    risk_score          FLOAT,          -- 0–100
    risk_level          VARCHAR(20),    -- LOW / MEDIUM / HIGH / CRITICAL
    collision_risk      FLOAT,          -- 0–100 component
    debris_risk         FLOAT,          -- 0–100 component
    altitude_risk       FLOAT,          -- 0–100 component
    orbit_type          VARCHAR(10),
    risk_drivers        TEXT,           -- JSON array of driver strings
    assessed_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingestion Logs: track every data pull
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id                  SERIAL PRIMARY KEY,
    source_name         VARCHAR(100) NOT NULL,
    records_ingested    INTEGER,
    status              VARCHAR(50) DEFAULT 'success',
    error_message       TEXT,
    ingested_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_satellites_norad_id     ON satellites(norad_id);
CREATE INDEX IF NOT EXISTS idx_satellites_object_name  ON satellites(object_name);
CREATE INDEX IF NOT EXISTS idx_orbital_params_sat_id   ON orbital_parameters(satellite_id);
CREATE INDEX IF NOT EXISTS idx_orbital_params_orbit    ON orbital_parameters(orbit_type);
CREATE INDEX IF NOT EXISTS idx_risk_sat_id             ON risk_assessments(satellite_id);
CREATE INDEX IF NOT EXISTS idx_risk_level              ON risk_assessments(risk_level);