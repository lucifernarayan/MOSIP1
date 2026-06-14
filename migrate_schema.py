"""
migrate_schema.py — Adds new columns to existing MOSIP tables.
Run once to upgrade from the initial schema to the full Phase 1 schema.

Usage: python migrate_schema.py
"""
from sqlalchemy import text
from backend.database.db import engine

MIGRATIONS = [
    # ── satellites: add new TLE columns ──────────────────────────────────────
    ("satellites.raan",
     "ALTER TABLE satellites ADD COLUMN IF NOT EXISTS raan FLOAT"),
    ("satellites.arg_of_perigee",
     "ALTER TABLE satellites ADD COLUMN IF NOT EXISTS arg_of_perigee FLOAT"),
    ("satellites.mean_anomaly",
     "ALTER TABLE satellites ADD COLUMN IF NOT EXISTS mean_anomaly FLOAT"),
    ("satellites.rev_at_epoch",
     "ALTER TABLE satellites ADD COLUMN IF NOT EXISTS rev_at_epoch INTEGER"),
    ("satellites.updated_at",
     "ALTER TABLE satellites ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),

    # ── orbital_parameters: add all derived columns ───────────────────────────
    ("orbital_parameters.altitude_km",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS altitude_km FLOAT"),
    ("orbital_parameters.apogee_km",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS apogee_km FLOAT"),
    ("orbital_parameters.perigee_km",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS perigee_km FLOAT"),
    ("orbital_parameters.semi_major_axis",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS semi_major_axis FLOAT"),
    ("orbital_parameters.raan",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS raan FLOAT"),
    ("orbital_parameters.arg_of_perigee",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS arg_of_perigee FLOAT"),
    ("orbital_parameters.period_minutes",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS period_minutes FLOAT"),
    ("orbital_parameters.orbit_type",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS orbit_type VARCHAR(10)"),
    ("orbital_parameters.created_at",
     "ALTER TABLE orbital_parameters ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),

    # ── risk_assessments: rename column + add new ones ────────────────────────
    # Note: generated_at → assessed_at (only if generated_at exists)
    ("risk_assessments.rename_generated_at",
     "ALTER TABLE risk_assessments RENAME COLUMN generated_at TO assessed_at"),
    ("risk_assessments.collision_risk",
     "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS collision_risk FLOAT"),
    ("risk_assessments.debris_risk",
     "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS debris_risk FLOAT"),
    ("risk_assessments.altitude_risk",
     "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS altitude_risk FLOAT"),
    ("risk_assessments.orbit_type",
     "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS orbit_type VARCHAR(10)"),
    ("risk_assessments.risk_drivers",
     "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS risk_drivers TEXT"),

    # ── ingestion_logs: add status and error columns ──────────────────────────
    ("ingestion_logs.rename_ingestion_time",
     "ALTER TABLE ingestion_logs RENAME COLUMN ingestion_time TO ingested_at"),
    ("ingestion_logs.status",
     "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'success'"),
    ("ingestion_logs.error_message",
     "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS error_message TEXT"),

    # ── Indexes ───────────────────────────────────────────────────────────────
    ("idx.orbital_orbit_type",
     "CREATE INDEX IF NOT EXISTS idx_orbital_params_orbit ON orbital_parameters(orbit_type)"),
    ("idx.risk_sat_id",
     "CREATE INDEX IF NOT EXISTS idx_risk_sat_id ON risk_assessments(satellite_id)"),
    ("idx.risk_level",
     "CREATE INDEX IF NOT EXISTS idx_risk_level ON risk_assessments(risk_level)"),
]

print("[MOSIP] Running migrations ...")
print()

success = 0
skipped = 0
failed  = 0

for name, sql in MIGRATIONS:
    # Each statement in its own transaction so one failure doesn't block the rest
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
        print(f"  [OK]    {name}")
        success += 1
    except Exception as e:
        err_str = str(e).split('\n')[0]
        if "already exists" in err_str or "does not exist" in err_str:
            print(f"  [SKIP]  {name}  ({err_str[:60]})")
            skipped += 1
        else:
            print(f"  [FAIL]  {name}")
            print(f"          {err_str[:80]}")
            failed += 1

print()
print(f"[MOSIP] Migration complete: {success} applied, {skipped} skipped, {failed} failed.")
