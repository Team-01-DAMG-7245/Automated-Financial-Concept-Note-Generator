from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.core.db import Base

class ConceptNoteRow(Base):
    __tablename__ = "concept_notes"

    id = Column(Integer, primary_key=True, index=True)
    concept = Column(String, nullable=False, unique=True, index=True)
    definition = Column(String, nullable=False)
    intuition = Column(String, nullable=False)
    formulae = Column(JSONB, nullable=False, default=list)
    step_by_step = Column(JSONB, nullable=False, default=list)
    pitfalls = Column(JSONB, nullable=False, default=list)
    examples = Column(JSONB, nullable=False, default=list)
    citations = Column(JSONB, nullable=False, default=list)
    used_fallback = Column(Boolean, nullable=False, default=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


