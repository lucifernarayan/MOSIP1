import json
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

# ==========================================
# CONFIG
# ==========================================

COLLECTION_NAME = "mosip_regulations"

# Local persistent Qdrant storage
client = QdrantClient(path="./qdrant_db")

# ==========================================
# FIND VECTOR SIZE
# ==========================================

metadata_path = Path("../metadata_chunks")

json_files = list(metadata_path.glob("*.json"))

if not json_files:
    raise Exception("No JSON files found in metadata_chunks!")

sample_file = json_files[0]

with open(sample_file, "r", encoding="utf-8") as f:
    sample_data = json.load(f)

vector_size = len(sample_data[0]["embedding"])

print(f"\nVector Size = {vector_size}")

# ==========================================
# CREATE COLLECTION
# ==========================================

if client.collection_exists(COLLECTION_NAME):
    print(f"\nDeleting old collection: {COLLECTION_NAME}")
    client.delete_collection(COLLECTION_NAME)

print(f"\nCreating collection: {COLLECTION_NAME}")

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=vector_size,
        distance=Distance.COSINE
    )
)

print("Collection Created Successfully")

# ==========================================
# LOAD ALL JSON FILES
# ==========================================

point_id = 0

for file in json_files:

    print(f"\nProcessing: {file.name}")

    with open(file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    points = []

    for chunk in chunks:

        points.append(
            PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload={
                    "source": chunk["source"],
                    "document": chunk["document"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"]
                }
            )
        )

        point_id += 1

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"Uploaded {len(points)} chunks")

# ==========================================
# VERIFY
# ==========================================

collection_info = client.get_collection(
    COLLECTION_NAME
)

print("\n===================================")
print("UPLOAD COMPLETE")
print("===================================")

print(f"Total vectors uploaded: {point_id}")
print(f"Collection name: {COLLECTION_NAME}")
print(collection_info)