from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.core.db import Base

class ConceptNoteRow(Base):
    __tablename__ = "concept_notes"

    id = Column(Integer, primary_key=True, index=True)
    concept = Column(String, nullable=False, unique=True, index=True)
    definition = Column(String, nullable=False)
    intuition = Column(String, nullable=False)
    formulae = Column(JSON, nullable=False, default=list)
    step_by_step = Column(JSON, nullable=False, default=list)
    pitfalls = Column(JSON, nullable=False, default=list)
    examples = Column(JSON, nullable=False, default=list)
    citations = Column(JSON, nullable=False, default=list)
    used_fallback = Column(Boolean, nullable=False, default=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


