from sqlalchemy import text
from backend.database.db import engine

with engine.connect() as conn:
    sats        = conn.execute(text("SELECT COUNT(*) FROM satellites")).scalar()
    risk        = conn.execute(text("SELECT COUNT(*) FROM risk_assessments")).scalar()
    avg_risk    = conn.execute(text("SELECT ROUND(AVG(risk_score)::numeric,2) FROM risk_assessments")).scalar()

    crit  = conn.execute(text("SELECT COUNT(*) FROM risk_assessments WHERE risk_level='CRITICAL'")).scalar()
    high  = conn.execute(text("SELECT COUNT(*) FROM risk_assessments WHERE risk_level='HIGH'")).scalar()
    med   = conn.execute(text("SELECT COUNT(*) FROM risk_assessments WHERE risk_level='MEDIUM'")).scalar()
    low   = conn.execute(text("SELECT COUNT(*) FROM risk_assessments WHERE risk_level='LOW'")).scalar()

    leo   = conn.execute(text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type='LEO'")).scalar()
    geo   = conn.execute(text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type='GEO'")).scalar()
    meo   = conn.execute(text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type='MEO'")).scalar()
    vleo  = conn.execute(text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type='VLEO'")).scalar()
    heo   = conn.execute(text("SELECT COUNT(*) FROM orbital_parameters WHERE orbit_type='HEO'")).scalar()

    top5  = conn.execute(text(
        "SELECT s.norad_id, s.object_name, r.risk_score, r.risk_level "
        "FROM risk_assessments r JOIN satellites s ON s.id=r.satellite_id "
        "ORDER BY r.risk_score DESC LIMIT 5"
    )).fetchall()

    logs  = conn.execute(text(
        "SELECT source_name, records_ingested FROM ingestion_logs ORDER BY ingested_at DESC LIMIT 3"
    )).fetchall()

print("satellites:", sats)
print("risk_assessments:", risk)
print("avg_risk:", avg_risk)
print("CRITICAL:", crit, " HIGH:", high, " MEDIUM:", med, " LOW:", low)
print("LEO:", leo, " GEO:", geo, " MEO:", meo, " VLEO:", vleo, " HEO:", heo)
print("top5:")
for r in top5:
    name = str(r[1])[:25] if r[1] else "?"
    print(f"  NORAD {r[0]}  {name:<26}  score={r[2]}  {r[3]}")
print("logs:", [(l[0], l[1]) for l in logs])
