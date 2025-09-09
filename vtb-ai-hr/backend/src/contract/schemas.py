from pydantic import BaseModel
from uuid import UUID


class InterviewRequestSchema(BaseModel):
    vacancy_uuid: UUID
    interview_uuid: UUID
    first_name: str
    last_name: str
    vacancy_bucket: str
    vacancy_filename: str
    resume_bucket: str
    resume_filename: str


class InterviewResultSchema(BaseModel):
    interview_uuid: UUID
    analysis_result: str
