from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

RAW_DIR = Path("../raw_text")
CHUNK_DIR = Path("../chunks")

CHUNK_DIR.mkdir(exist_ok=True)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)

txt_files = list(RAW_DIR.glob("*.txt"))

print(f"\nFound {len(txt_files)} text files\n")

for txt_file in txt_files:

    print(f"Processing: {txt_file.name}")

    text = txt_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    chunks = splitter.split_text(text)

    records = []

    for idx, chunk in enumerate(chunks):

        records.append({
            "chunk_id": idx,
            "source_document": txt_file.stem,
            "text": chunk
        })

    output_file = (
        CHUNK_DIR /
        f"{txt_file.stem}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            records,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Created {len(records)} chunks"
    )

print("\nChunking Complete!")