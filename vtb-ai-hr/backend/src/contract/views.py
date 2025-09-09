import json
from uuid import UUID

from candidate.models import Candidate
from common.models import User
from database import Session
from fastapi import HTTPException
from recruiter.models import Interview, Recruiter, Vacancy
from sqlalchemy import select, update

from .router import router
from .schemas import InterviewRequestSchema, InterviewResultSchema


@router.get("/interview_requests/get/{interview_id}", tags=["Contracts"])
def get_interview_request(interview_id: UUID) -> InterviewRequestSchema:
    with Session() as session:
        interview = session.execute(
            select(Interview).where(Interview.id == interview_id)
        ).scalar_one_or_none()
        if not interview:
            raise HTTPException(status_code=405, detail="Interview not found")

        vacancy = session.execute(
            select(Vacancy).where(Vacancy.id == interview.vacancy_id)
        ).scalar_one_or_none()
        if not vacancy:
            raise HTTPException(
                status_code=406, detail="Vacancy not found for interview"
            )

        candidate_user = session.execute(
            select(User)
            .join(Candidate, Candidate.id == User.id)
            .where(Candidate.id == interview.candidate_id)
        ).scalar_one_or_none()
        candidate = session.execute(
            select(Candidate).where(Candidate.id == interview.candidate_id)
        ).scalar_one_or_none()
        if not candidate_user or not candidate:
            raise HTTPException(
                status_code=407, detail="Candidate not found for interview"
            )

        vacancy_bucket = vacancy.bucket_name or ""
        vacancy_filename = vacancy.filename or ""
        resume_filename = candidate.resume or ""

        if not vacancy_bucket or not vacancy_filename or not resume_filename:
            raise HTTPException(
                status_code=408,
                detail="Not all necessary info was provided by either candidate or recruiter",
            )

        return InterviewRequestSchema(
            vacancy_uuid=vacancy.id,
            interview_uuid=interview.id,
            first_name=candidate_user.first_name,
            last_name=candidate_user.last_name,
            vacancy_bucket=vacancy_bucket,
            vacancy_filename=vacancy_filename,
            resume_bucket="resume",
            resume_filename=resume_filename,
        )


@router.post("/interviews/{id}/assign_report", tags=["Contracts"])
def interview_assign_report(id: UUID, interview_result: InterviewResultSchema):
    with Session() as session:
        session.execute(
            update(Interview)
            .where(Interview.id == id)
            .values(
                report_json=interview_result.analysis_result,
                report_score=json.loads(interview_result.analysis_result)[
                    "total_match_percent"
                ],
            )
        )
        session.commit()
