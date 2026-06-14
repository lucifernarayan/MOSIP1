import fitz
from pathlib import Path

# Paths
DATA_DIR = Path("../data")
OUTPUT_DIR = Path("../raw_text")

# Create output folder if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

print("\nStarting PDF extraction...\n")

# Find all PDFs recursively
pdf_files = list(DATA_DIR.rglob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files\n")

for pdf_file in pdf_files:

    try:
        # Skip empty files
        if pdf_file.stat().st_size == 0:
            print(f"Skipping empty file: {pdf_file.name}")
            continue

        print(f"Reading: {pdf_file.name}")

        doc = fitz.open(pdf_file)

        text = ""

        for page_num, page in enumerate(doc):
            text += page.get_text()

        doc.close()

        # Skip PDFs with no extractable text
        if not text.strip():
            print(
                f"No text found in {pdf_file.name} "
                "(might be scanned PDF, OCR needed)"
            )
            continue

        output_file = OUTPUT_DIR / f"{pdf_file.stem}.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        print(
            f"Saved: {output_file.name} "
            f"({len(text):,} characters)"
        )

    except Exception as e:
        print(
            f"Error processing {pdf_file.name}: {e}"
        )

print("\nExtraction Complete!")