"""
rag_service.py
--------------
Unified search layer for MOSIP regulatory knowledge base.
Uses a lightweight, high-performance, memory-efficient pure Python TF-IDF engine
to run on resource-constrained hosting (e.g. Render free tier 512MB RAM).
"""

import os
import json
import math
import re
import logging
from qdrant_client import QdrantClient
from backend.config import QDRANT_PATH, QDRANT_COLLECTION

logger = logging.getLogger(__name__)

# ── Qdrant client (for health checks only) ────────────────────────────────────
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = QdrantClient(path=QDRANT_PATH)
    return _client

# ── Pure-Python Memory-Efficient TF-IDF RAG Engine ──────────────────────────
_chunks = None

def _load_chunks():
    global _chunks
    if _chunks is not None:
        return _chunks
    
    _chunks = []
    # Search in regulations/chunks/ relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    chunks_dir = os.path.join(os.path.dirname(current_dir), "regulations", "chunks")
    
    # Fallback to local path relative to working directory
    if not os.path.exists(chunks_dir):
        chunks_dir = "regulations/chunks"
        
    if os.path.exists(chunks_dir):
        logger.info(f"Loading RAG regulations from: {chunks_dir}")
        for filename in os.listdir(chunks_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(chunks_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                _chunks.append({
                                    "text": item.get("text", ""),
                                    "document": item.get("source_document", filename.replace(".json", "")),
                                    "source": item.get("source_document", filename.replace(".json", ""))
                                })
                except Exception as e:
                    logger.error(f"Error loading chunk file {filename}: {e}")
    else:
        logger.error(f"Regulations chunks directory not found at: {chunks_dir}")
        
    logger.info(f"Loaded {len(_chunks)} regulations chunks successfully.")
    return _chunks

def tokenize(text: str) -> list[str]:
    # Extract lowercased words of length >= 3
    return re.findall(r"\b\w{3,}\b", text.lower())

# ── Core search ───────────────────────────────────────────────────────────────

def search_regulations(question: str, top_k: int = 5) -> list[dict]:
    """
    Search over the regulatory knowledge base using memory-efficient TF-IDF.
    """
    chunks = _load_chunks()
    if not chunks:
        return []
        
    query_terms = tokenize(question)
    if not query_terms:
        return []
        
    # Calculate Document Frequency (DF) for query terms
    df = {}
    for term in query_terms:
        df[term] = sum(1 for c in chunks if term in c["text"].lower())
        
    N = len(chunks)
    scored_results = []
    
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        score = 0.0
        
        for term in query_terms:
            tf = text_lower.count(term)
            if tf > 0:
                # Smoothed Inverse Document Frequency (IDF)
                idf = math.log(1.0 + N / (1.0 + df[term]))
                score += tf * idf
                
                # Boost if term appears in document title
                if term in chunk["document"].lower():
                    score += 5.0 * idf
                    
        if score > 0:
            scored_results.append({
                "score": round(score, 4),
                "source": chunk["source"],
                "document": chunk["document"],
                "text": chunk["text"]
            })
            
    # Sort by score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Normalize score to 0.0 - 1.0 range
    if scored_results:
        max_score = scored_results[0]["score"]
        for r in scored_results:
            r["score"] = round(r["score"] / max_score, 4)
            
    return scored_results[:top_k]


def build_compliance_queries(satellite_data: dict) -> list[str]:
    """
    Generate contextual regulation search queries from satellite orbital data.
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