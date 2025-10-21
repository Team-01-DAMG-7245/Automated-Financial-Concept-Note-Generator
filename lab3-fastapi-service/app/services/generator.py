import os
import instructor
from typing import List, Dict
from openai import OpenAI
from app.models.schemas import ConceptNote, Citation, RetrievedChunk

MODEL = os.getenv("GENERATION_MODEL", "gpt-4.1-mini")

_client = instructor.from_openai(
    OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
    mode=instructor.Mode.JSON,
)

_SYSTEM = (
    "You generate standardized, concise finance concept notes based ONLY on the provided context. "
    "Be precise, avoid hallucinations, include plaintext formulae when relevant, and attach citations."
)

def _build_prompt(concept: str, contexts: List[Dict]) -> str:
    lines = [f"CONCEPT: {concept}", "", "CONTEXT CHUNKS:"]
    for c in contexts:
        meta = []
        if c.get("source_type"): meta.append(f"type={c['source_type']}")
        if c.get("title"): meta.append(f"title={c['title']}")
        if c.get("page") is not None: meta.append(f"page={c['page']}")
        if c.get("url"): meta.append(f"url={c['url']}")
        if c.get("score") is not None: meta.append(f"score={c['score']:.3f}")
        lines.append(f"[{'; '.join(meta)}]\n{c['text']}\n")
    lines.append(
        "TASK: Return a JSON object with fields: concept, definition, intuition, formulae[], "
        "step_by_step[], pitfalls[], examples[], citations[], used_fallback."
    )
    return "\n".join(lines)

def generate_concept_note(concept_name: str, chunks: List[RetrievedChunk]) -> ConceptNote:
    # map your RetrievedChunk -> generic context dict
    contexts = []
    for ch in chunks:
        md = ch.metadata or {}
        contexts.append({
            "text": ch.content,
            "source_type": md.get("source_type", "pdf"),
            "title": md.get("title"),
            "page": md.get("page"),
            "url": md.get("url"),
            "score": ch.score,
        })

    used_fallback = any(c.get("source_type") == "wikipedia" for c in contexts)
    prompt = _build_prompt(concept_name, contexts)

    note: ConceptNote = _client.chat.completions.create(
        model=MODEL,
        response_model=ConceptNote,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    note.used_fallback = used_fallback
    return note
