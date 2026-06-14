from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# ==================================
# Load Embedding Model
# ==================================

print("Loading Embedding Model...")

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

# ==================================
# Connect Local Qdrant
# ==================================

client = QdrantClient(
    path="./qdrant_db"
)

COLLECTION_NAME = "mosip_regulations"

print("Connected to Qdrant")

# ==================================
# Ask Question
# ==================================

query = input("\nAsk MOSIP: ")

# ==================================
# Create Query Embedding
# ==================================

query_embedding = model.encode(
    query,
    normalize_embeddings=True
).tolist()

# ==================================
# Search Qdrant
# ==================================

try:

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=5
    ).points

    if len(results) == 0:
        print("\nNo matching regulations found.")
        exit()

    print("\n" + "=" * 100)
    print("MOSIP KNOWLEDGE RETRIEVAL RESULTS")
    print("=" * 100)

    for i, result in enumerate(results, start=1):

        print(f"\nResult #{i}")
        print("-" * 100)

        print(f"Source     : {result.payload.get('source', 'N/A')}")
        print(f"Document   : {result.payload.get('document', 'N/A')}")
        print(f"Chunk ID   : {result.payload.get('chunk_id', 'N/A')}")
        print(f"Similarity : {round(result.score, 4)}")

        print("\nRetrieved Context:\n")

        print(result.payload.get("text", "")[:1200])

        print("\n")

except Exception as e:

    print("\nERROR:")
    print(e)