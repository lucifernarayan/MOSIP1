from fastapi import APIRouter, Query
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY, GROQ_MODEL
from knowledge_layer.rag_service import search_regulations

router = APIRouter()


@router.get("/search", summary="Search compliance regulations")
def search(
    q: str = Query(..., description="Query text to search semantically"),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Runs a semantic search query against the Qdrant regulations database
    using the sentence embedding model.
    """
    try:
        results = search_regulations(q, top_k=limit)
        return {"query": q, "results": results}
    except Exception as e:
        return {"query": q, "results": [], "error": str(e)}


@router.get("/ask", summary="Ask a grounded regulation question")
def ask(
    q: str = Query(..., min_length=3, description="Question to answer from Qdrant regulation context"),
    limit: int = Query(5, ge=1, le=10),
):
    """
    Retrieves regulation chunks from Qdrant and asks the configured LLM to answer
    only from that retrieved context.
    """
    results = search_regulations(q, top_k=limit)
    context = "\n\n".join(
        f"[{i + 1}] {item.get('source', '')} {item.get('document', '')}\n{item.get('text', '')}"
        for i, item in enumerate(results)
    )

    if not GROQ_API_KEY:
        return {
            "query": q,
            "answer": "LLM is not configured. Set GROQ_API_KEY to enable grounded regulation answers.",
            "results": results,
            "status": "llm_not_configured",
        }

    try:
        llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.1, max_tokens=700)
        response = llm.invoke([
            SystemMessage(content=(
                "You are MOSIP's regulatory intelligence assistant. Answer only from the supplied "
                "ESA/IADC regulatory context. If the answer is not present, say that the retrieved "
                "context does not contain enough evidence. Cite sources by bracket number."
            )),
            HumanMessage(content=f"Question: {q}\n\nRetrieved context:\n{context}"),
        ])
        return {
            "query": q,
            "answer": response.content.strip(),
            "results": results,
            "status": "complete",
        }
    except Exception as e:
        return {
            "query": q,
            "answer": "",
            "results": results,
            "error": str(e),
            "status": "error",
        }
