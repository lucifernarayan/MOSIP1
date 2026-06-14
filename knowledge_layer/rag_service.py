"""
rag_service.py
--------------
Unified Qdrant search layer for MOSIP regulatory knowledge base.
Connects to the local persistent Qdrant store populated with
ESA / IADC / NASA regulatory document embeddings.
"""

import logging
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from backend.config import QDRANT_PATH, QDRANT_COLLECTION

logger = logging.getLogger(__name__)

# ── Embedding model (same one used during upload) ────────────────────────────
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model

# ── Qdrant client (absolute path from config, not fragile relative path) ─────
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = QdrantClient(path=QDRANT_PATH)
    return _client


# ── Core search ───────────────────────────────────────────────────────────────

def search_regulations(question: str, top_k: int = 5) -> list[dict]:
    """
    Semantic search over the regulatory knowledge base.

    Returns a list of dicts with keys:
        score, source, document, text
    """
    model  = _get_model()
    client = _get_client()

    query_embedding = model.encode(
        question,
        normalize_embeddings=True
    ).tolist()

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_embedding,
        limit=top_k,
    ).points

    return [
        {
            "score":    round(result.score, 4),
            "source":   result.payload.get("source", ""),
            "document": result.payload.get("document", ""),
            "text":     result.payload.get("text", ""),
        }
        for result in results
    ]


def build_compliance_queries(satellite_data: dict) -> list[str]:
    """
    Generate contextual regulation search queries from satellite orbital data.
    Used to retrieve the most relevant regulatory chunks before LLM reasoning.
    """
    orbit_type = satellite_data.get("orbit_type", "LEO")
    altitude   = satellite_data.get("altitude_km", 0)
    risk_level = satellite_data.get("risk_level", "UNKNOWN")

    queries = [
        f"{orbit_type} satellite post-mission disposal requirements",
        f"deorbit 25-year rule {orbit_type} compliance",
        "casualty risk limit debris reentry",
        f"passivation requirements {orbit_type}",
    ]

    if risk_level in ("HIGH", "CRITICAL"):
        queries.append("active debris removal high risk object mitigation")
        queries.append("collision avoidance maneuver requirements")

    if altitude and altitude < 600:
        queries.append("very low earth orbit VLEO deorbit lifetime atmospheric drag")

    if orbit_type == "GEO":
        queries.append("geostationary graveyard orbit disposal GEO")

    return queries


def get_applicable_regulations(satellite_data: dict, top_k: int = 4) -> list[dict]:
    """
    Run multiple contextual queries and deduplicate results by chunk text.
    Returns the top regulations most applicable to this satellite.
    """
    queries  = build_compliance_queries(satellite_data)
    seen     = set()
    combined = []

    for q in queries:
        results = search_regulations(q, top_k=top_k)
        for r in results:
            key = r["text"][:120]          # deduplicate by first 120 chars
            if key not in seen:
                seen.add(key)
                combined.append(r)

    # Sort by score descending, return top 10
    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[:10]


def search_topic(topic: str, top_k: int = 5) -> list[dict]:
    """Convenience wrapper for single-topic search."""
    return search_regulations(topic, top_k=top_k)


def qdrant_healthy() -> bool:
    """Quick health check — returns True if Qdrant collection is reachable."""
    try:
        client = _get_client()
        return client.collection_exists(QDRANT_COLLECTION)
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}", exc_info=True)
        return False