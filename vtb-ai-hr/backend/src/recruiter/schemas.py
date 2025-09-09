from typing import Optional
from common.schemas import UserSchema
from pydantic import BaseModel, FutureDatetime
from uuid import UUID


class RecruiterSchema(UserSchema):
    department: str


class VacancySchema(BaseModel):
    id: Optional[UUID] = None
    recruiter_id: UUID
    description: str
    position: str
    keywords: str
    bucket_name: Optional[str] = None
    filename: Optional[str] = None
    expires_at: FutureDatetime


class InterviewSchema(BaseModel):
    id: Optional[UUID] = None
    candidate_id: UUID
    vacancy_id: UUID
    start_time: Optional[FutureDatetime] = None
    report_json: Optional[str] = None
    report_score: Optional[float] = None
    verdict: Optional[str] = None
    description: str
    conference_id: str
