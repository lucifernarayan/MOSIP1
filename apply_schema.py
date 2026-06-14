"""
apply_schema.py — Run once to create all MOSIP tables in PostgreSQL.
Usage: python apply_schema.py
"""
from sqlalchemy import text
from backend.database.db import engine

with open("backend/database/schema.sql", "r", encoding="utf-8") as f:
    raw_sql = f.read()

# Split on semicolons, skip empty/comment-only statements
statements = [s.strip() for s in raw_sql.split(";") if s.strip() and not s.strip().startswith("--")]

print("[MOSIP] Applying schema ...")

with engine.begin() as conn:
    for stmt in statements:
        try:
            conn.execute(text(stmt))
            # Print just the first line so output is readable
            print(f"  [OK]  {stmt.splitlines()[0][:72]}")
        except Exception as e:
            print(f"  [ERR] {stmt.splitlines()[0][:72]}")
            print(f"       Error: {e}")

print("\n[MOSIP] Schema applied successfully.")
