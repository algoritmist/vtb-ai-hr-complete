import uuid
from datetime import datetime

from database import Base
from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

MAX_STR_LEGNTH = 8096

MAX_DESCRIPTION_LENGTH = 8096


class Recruiter(Base):

    __tablename__ = "recruiters"

    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="recruiter")

    department: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=False
    )


class Vacancy(Base):

    __tablename__ = "vacancies"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id"), nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(MAX_DESCRIPTION_LENGTH), nullable=False
    )
    position: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=False
    )

    keywords: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=False
    )

    bucket_name: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=True
    )
    filename: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=True
    )

    creation_date: Mapped[datetime] = Column(DateTime, default=datetime.now())
    expires_at: Mapped[datetime] = Column(DateTime, nullable=False)


class Interview(Base):

    __tablename__ = "interviews"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidates.id"), nullable=False
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("vacancies.id"), nullable=False
    )

    start_time: Mapped[datetime] = Column(DateTime, nullable=True)

    report_json: Mapped[str] = mapped_column(
        String(MAX_DESCRIPTION_LENGTH), nullable=True
    )
    report_score: Mapped[float] = mapped_column(Float, nullable=True)
    verdict: Mapped[str] = mapped_column(String(MAX_STR_LEGNTH), nullable=True)

    conference_id: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(MAX_STR_LEGNTH), nullable=False
    )
