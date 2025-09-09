from database import Base
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

MAX_STR_LEGNTH = 8096


class Candidate(Base):

    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="candidate")

    resume: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=True
    )  # link to resume in S3 storage
