import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("level_id", "order_index", name="uq_modules_level_order"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("levels.id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    level: Mapped["Level"] = relationship(back_populates="modules")  # noqa: F821
    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        back_populates="module", order_by="Lesson.order_index"
    )
