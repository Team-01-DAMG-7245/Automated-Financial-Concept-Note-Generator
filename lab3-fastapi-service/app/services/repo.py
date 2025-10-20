from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.models.tables import ConceptNoteRow
from app.models.schemas import ConceptNote

def get_cached_concept(db: Session, concept: str):
    q = select(ConceptNoteRow).where(ConceptNoteRow.concept == concept)
    return db.execute(q).scalar_one_or_none()

def upsert_concept_note(db: Session, note: ConceptNote) -> ConceptNoteRow:
    stmt = insert(ConceptNoteRow).values(
        concept=note.concept,
        definition=note.definition,
        intuition=note.intuition,
        formulae=note.formulae,
        step_by_step=note.step_by_step,
        pitfalls=note.pitfalls,
        examples=note.examples,
        citations=[c.model_dump() for c in note.citations],
        used_fallback=note.used_fallback,
        generated_at=note.generated_at,
    ).on_conflict_do_update(
        index_elements=[ConceptNoteRow.concept],
        set_={
            "definition": stmt.excluded.definition,
            "intuition": stmt.excluded.intuition,
            "formulae": stmt.excluded.formulae,
            "step_by_step": stmt.excluded.step_by_step,
            "pitfalls": stmt.excluded.pitfalls,
            "examples": stmt.excluded.examples,
            "citations": stmt.excluded.citations,
            "used_fallback": stmt.excluded.used_fallback,
            "generated_at": stmt.excluded.generated_at,
        },
    ).returning(ConceptNoteRow)
    return db.execute(stmt).scalar_one()
