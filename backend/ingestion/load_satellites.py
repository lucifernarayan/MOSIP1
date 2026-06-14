import json
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:ujjwal@localhost:5432/mosip"

engine = create_engine(DATABASE_URL)

with open("data/satellites.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

print("Records loaded:", len(df))