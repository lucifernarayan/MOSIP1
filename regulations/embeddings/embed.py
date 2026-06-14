from sentence_transformers import SentenceTransformer
import json
from pathlib import Path

INPUT_DIR = Path("../metadata_chunks")

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

json_files = list(INPUT_DIR.glob("*.json"))

print(f"Found {len(json_files)} files")

for file in json_files:

    with open(file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"\nEmbedding {file.name}")

    for chunk in chunks:

        embedding = model.encode(
            chunk["text"],
            normalize_embeddings=True
        )

        chunk["embedding"] = embedding.tolist()

    with open(file, "w", encoding="utf-8") as f:
        json.dump(
            chunks,
            f,
            ensure_ascii=False
        )

    print(
        f"Done: {file.name}"
    )