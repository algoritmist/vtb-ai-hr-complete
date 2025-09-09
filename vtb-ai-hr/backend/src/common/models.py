import uuid

from database import Base
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

MAX_STR_LENGTH = 8096
HASHED_STR_LENGTH = 255


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    candidate = relationship("Candidate", back_populates="user")
    recruiter = relationship("Recruiter", back_populates="user")

    first_name: Mapped[str] = mapped_column(
        String(MAX_STR_LENGTH), nullable=False
    )
    second_name: Mapped[str] = mapped_column(
        String(MAX_STR_LENGTH), nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(MAX_STR_LENGTH), nullable=False
    )

    login: Mapped[str] = mapped_column(
        String(MAX_STR_LENGTH), nullable=False, unique=True
    )
    password: Mapped[bytes] = mapped_column(
        String(HASHED_STR_LENGTH), nullable=False
    )

    photo: Mapped[str] = mapped_column(
        String(MAX_STR_LENGTH), nullable=True
    )  # link to user photo in S3 storage
