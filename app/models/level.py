import uuid

from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.learning_profile import CEFRLevel, cefr_level_type


class Level(Base):
    """A CEFR level (A1/A2/B1/B2) — the top of the course tree."""

    __tablename__ = "levels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[CEFRLevel] = mapped_column(cefr_level_type, unique=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    modules: Mapped[list["Module"]] = relationship(  # noqa: F821
        back_populates="level", order_by="Module.order_index"
    )
