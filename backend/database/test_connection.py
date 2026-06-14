from sqlalchemy import text
from backend.database.db import engine

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT current_database();")
    )

    print(result.fetchone())