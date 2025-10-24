import os
import json
import requests
import streamlit as st

st.set_page_config(page_title="Aurelia — Financial Concept Notes", layout="wide")
st.title("📘 Aurelia — Financial Concept Notes")
st.caption("Streamlit frontend connected to FastAPI RAG backend")

default_backend = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
backend_url = st.sidebar.text_input("Backend URL:", default_backend)

col1, col2 = st.columns([3, 1])
with col1:
    concept = st.text_input("Enter a financial concept", "Sharpe Ratio")
with col2:
    top_k = st.slider("Top-K Chunks (for retrieval)", 1, 10, 3)

c1, c2 = st.columns([1, 1])
with c1:
    if st.button("💾 Seed / Refresh Cache"):
        try:
            payload = {
                "concept_name": concept,  # ← ADD THIS LINE
                "sources": [
                    {"type": "web", "uri": "https://en.wikipedia.org/wiki/Sharpe_ratio"},
                    {"type": "web", "uri": "https://www.investopedia.com/terms/s/sharperatio.asp"},
                ],
                "rebuild": False,
            }
            r = requests.post(f"{backend_url}/api/v1/seed", json=payload, timeout=180)
            st.success(f"POST /api/v1/seed → {r.status_code}\n{r.text}")
        except Exception as e:
            st.error(f"Seed failed: {e}")

with c2:
    do_query = st.button("🔍 Query / Generate Note")

def normalize_note(data: dict, fallback_concept: str) -> dict:
    if "generated_note" in data and isinstance(data["generated_note"], dict):
        return data["generated_note"]

    if "note" in data and isinstance(data["note"], dict):
        note = data["note"]
        return {
            "concept": note.get("title", fallback_concept),
            "definition": note.get("definition"),
            "intuition": note.get("intuition"),
            "formulae": note.get("formulae") or note.get("formula"),
            "examples": note.get("examples"),
            "citations": note.get("citations"),
            "content": note.get("content"),
        }

    return {
        "concept": data.get("concept", fallback_concept),
        "definition": data.get("definition"),
        "intuition": data.get("intuition"),
        "formulae": data.get("formulae") or data.get("formula"),
        "examples": data.get("examples"),
        "citations": data.get("citations"),
        "content": data.get("content"),
    }

if do_query:
    with st.spinner("Querying backend and generating concept note…"):
        try:
            resp = requests.post(
                f"{backend_url}/api/v1/query",
                json={"concept_name": concept, "top_k": top_k},
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"POST /api/v1/query → {resp.status_code} — OK")

                meta_cols = st.columns(3)
                with meta_cols[0]:
                    st.markdown(f"**Source:** `{data.get('source', 'Unknown')}`")
                with meta_cols[1]:
                    if data.get("vector_db"):
                        st.markdown(f"**Vector DB:** `{data.get('vector_db')}`")
                with meta_cols[2]:
                    st.markdown(f"**Backend:** `{backend_url}`")

                tab1, tab2 = st.tabs(["Generated Note", "Retrieved Chunks (Debug)"])

                with tab1:
                    note = normalize_note(data, concept)

                    st.subheader(note.get("concept", concept))
                    st.markdown(f"**Definition:** {note.get('definition', 'N/A')}")
                    st.markdown(f"**Intuition:** {note.get('intuition', 'N/A')}")

                    formulae = note.get("formulae")
                    if formulae:
                        st.markdown("**Formulae:**")
                        if isinstance(formulae, list):
                            st.code("\n".join([str(f) for f in formulae]))
                        else:
                            st.code(str(formulae))

                    examples = note.get("examples")
                    if examples:
                        st.markdown("**Examples:**")
                        for ex in (examples if isinstance(examples, list) else [examples]):
                            st.markdown(f"- {ex}")

                    citations = note.get("citations")
                    if citations:
                        st.markdown("**Citations:**")
                        for c in citations:
                            if isinstance(c, dict):
                                src = c.get("source") or c.get("source_type") or "source"
                                pg = c.get("page") or c.get("section") or ""
                                sc = c.get("score")
                                suffix = f" — p.{pg}" if pg else ""
                                score = f" (score {sc})" if sc is not None else ""
                                st.markdown(f"- {src}{suffix}{score}")
                            else:
                                st.markdown(f"- {c}")

                    if note.get("content"):
                        st.markdown("---")
                        st.markdown(note["content"])

                with tab2:
                    chunks = data.get("retrieved_chunks") or data.get("chunks") or []
                    st.json(chunks)

            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")
