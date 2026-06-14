from dotenv import load_dotenv
import os

load_dotenv()

# ── PostgreSQL ────────────────────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "mosip")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ── Qdrant (local persistent vector store) ────────────────────────────────────
QDRANT_PATH       = os.getenv("QDRANT_PATH", "regulations/qdrant/qdrant_db")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "mosip_regulations")

# ── Groq LLM ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")