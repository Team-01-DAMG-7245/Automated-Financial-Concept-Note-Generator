from typing import List
from app.models.schemas import RetrievedChunk
from app.services.rag_service import RAGService

_rag = RAGService()

def retrieve_from_vector_store(concept_name: str, top_k: int) -> List[RetrievedChunk]:
    """
    Expect RAGService to return items with fields: content, metadata, score.
    If names differ, map them here.
    """
    raw = _rag.retrieve(concept_name, top_k=top_k)
    chunks: List[RetrievedChunk] = []
    for r in raw:
        chunks.append(RetrievedChunk(
            content=r.get("content") or r.get("text") or "",
            metadata=r.get("metadata") or {},
            score=r.get("score"),
        ))
    return chunks

def wikipedia_fallback(concept_name: str) -> List[RetrievedChunk]:
    from app.services.wikipedia_fallback import search_wikipedia  # adjust to your function name
    raw = search_wikipedia(concept_name)  # should return list[dict]
    out: List[RetrievedChunk] = []
    for r in raw:
        md = r.get("metadata", {})
        md.setdefault("source_type", "wikipedia")
        out.append(RetrievedChunk(
            content=r.get("content") or r.get("text") or "",
            metadata=md,
            score=r.get("score"),
        ))
    return out
