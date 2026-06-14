import json
from pathlib import Path

CHUNK_DIR = Path("../chunks")
OUTPUT_DIR = Path("../metadata_chunks")

OUTPUT_DIR.mkdir(exist_ok=True)

json_files = list(CHUNK_DIR.glob("*.json"))

print(f"\nFound {len(json_files)} chunk files\n")

for file in json_files:

    with open(file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    enriched_chunks = []

    filename = file.stem

    # Detect source
    if "ESA" in filename.upper():
        source = "ESA"

    elif "IADC" in filename.upper():
        source = "IADC"

    elif "NASA" in filename.upper():
        source = "NASA"

    else:
        source = "UNKNOWN"

    for chunk in chunks:

        enriched_chunks.append({
            "chunk_id": chunk["chunk_id"],
            "source": source,
            "document": filename,
            "text": chunk["text"]
        })

    output_file = OUTPUT_DIR / file.name

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            enriched_chunks,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Processed {filename}"
    )

print("\nMetadata generation complete!")