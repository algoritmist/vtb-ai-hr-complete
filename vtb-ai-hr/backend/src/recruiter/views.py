import io
from uuid import UUID
import uuid

from fastapi import HTTPException, Depends, UploadFile, File
from fastapi_pagination import Page, Params
from recruiter.models import Recruiter, Vacancy, Interview
from .schemas import (
    RecruiterSchema,
    VacancySchema,
    InterviewSchema
)
from database import Session
from sqlalchemy import insert, select, update
from pydantic import PastDatetime
from minio import Minio
from minio.error import S3Error

from common.models import User

from .router import router

from fastapi_pagination.ext.sqlalchemy import paginate


@router.post("/recruiters/create", status_code=201, tags=["Recruiters"])
def recruiter_create(recruiter: RecruiterSchema):
    with Session() as session:
        query1 = (
            insert(User)
            .values(
                first_name=recruiter.first_name,
                second_name=recruiter.second_name,
                last_name=recruiter.last_name,
                login=recruiter.login,
                password=recruiter.password,
                photo=recruiter.photo or None,
            )
            .returning(User.id)
        )
        result1 = session.execute(query1)
        session.flush()
        user_id = result1.scalar()
        query2 = insert(Recruiter).values(
            id=user_id, department=recruiter.department)
        session.execute(query2)
        session.commit()
        return user_id


@router.post("/vacancies/create", status_code=201, tags=["Recruiters"])
def vacancy_create(vacancy: VacancySchema):
    with Session() as session:
        result = session.execute(
            insert(Vacancy)
            .values(
                recruiter_id=vacancy.recruiter_id,
                description=vacancy.description,
                position=vacancy.position,
                keywords=vacancy.keywords,
                bucket_name=vacancy.bucket_name,
                filename=vacancy.filename,
                expires_at=vacancy.expires_at,
            )
            .returning(Vacancy.id)
        )
        vacancy_id = result.scalar()
        session.commit()
        return vacancy_id


@router.get("/vacancies/{id}/ranking", tags=["Recruiters"])
def vacancies_ranking(id: UUID) -> Page[InterviewSchema]:
    return paginate(Session(), select(Interview).where(Interview.vacancy_id ==
                                                       id).order_by(Interview.report_score),
                    params=Params(page=1, size=50))


@router.post("/interviews/create", status_code=201, tags=["Recruiters"])
def interview_create(interview: InterviewSchema):
    with Session() as session:
        result = session.execute(
            insert(Interview)
            .values(
                candidate_id=interview.candidate_id,
                vacancy_id=interview.vacancy_id,
                start_time=interview.start_time,
                description=interview.description,
                conference_id=interview.conference_id,
            )
            .returning(Interview.id)
        )
        interview_id = result.scalar()
        session.commit()
        return interview_id


@router.post("/interviews/{id}/assign_time", tags=["Recruiters"])
def interview_assign_time(id: UUID, date_time: PastDatetime):
    with Session() as session:
        session.execute(
            update(Interview).where(Interview.id ==
                                    id).values(start_time=date_time)
        )
        session.commit()


@router.post("/interviews/{id}/assign_conference", tags=["Recruiters", "AI-HR"])
def interview_assign_conference(id: UUID, conference_id: str):
    with Session() as session:
        session.execute(
            update(Interview)
            .where(Interview.id == id)
            .values(conference_id=conference_id)
        )
        session.commit()


# READ operations
@router.get("/recruiters/{id}", tags=["Recruiters"])
def recruiter_get(id: UUID) -> RecruiterSchema:
    with Session() as session:
        result = session.execute(
            select(Recruiter, User)
            .join(User, Recruiter.id == User.id)
            .where(Recruiter.id == id)
        )
        recruiter_data, user_data = result.first()
        if not recruiter_data:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        return RecruiterSchema(
            first_name=user_data.first_name,
            second_name=user_data.second_name,
            last_name=user_data.last_name,
            login=user_data.login,
            password=user_data.password,
            photo=user_data.photo,
            department=recruiter_data.department
        )


@router.get("/vacancies/{id}", tags=["Recruiters"])
def vacancy_get(id: UUID) -> VacancySchema:
    with Session() as session:
        result = session.execute(
            select(Vacancy).where(Vacancy.id == id)
        )
        vacancy = result.scalar_one_or_none()
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")

        return VacancySchema(
            recruiter_id=vacancy.recruiter_id,
            description=vacancy.description,
            position=vacancy.position,
            keywords=vacancy.keywords,
            bucket_name=vacancy.bucket_name,
            filename=vacancy.filename,
            expires_at=vacancy.expires_at
        )


@router.get("/interviews/{id}", tags=["Recruiters"])
def interview_get(id: UUID) -> InterviewSchema:
    with Session() as session:
        result = session.execute(
            select(Interview).where(Interview.id == id)
        )
        interview = result.scalar_one_or_none()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        return InterviewSchema(
            id=interview.id,
            candidate_id=interview.candidate_id,
            vacancy_id=interview.vacancy_id,
            start_time=interview.start_time,
            report_json=interview.report_json,
            report_score=interview.report_score,
            verdict=interview.verdict,
            description=interview.description,
            conference_id=interview.conference_id
        )


# LIST operations with pagination
@router.get("/recruiters", tags=["Recruiters"])
def recruiters_list(params: Params = Depends()) -> Page[RecruiterSchema]:
    with Session() as session:
        query = select(User, Recruiter).join(
            Recruiter, Recruiter.id == User.id)

        def transformer(items):
            return [
                RecruiterSchema(
                    id=user.id,
                    first_name=user.first_name,
                    second_name=user.second_name,
                    last_name=user.last_name,
                    login=user.login,
                    photo=user.photo,
                    department=recruiter.department
                )
                for user, recruiter in items
            ]

        return paginate(session, query, params, transformer=transformer)


@router.get("/vacancies", tags=["Recruiters"])
def vacancies_list(params: Params = Depends()) -> Page[VacancySchema]:
    with Session() as session:
        query = select(Vacancy)
        return paginate(session, query, params)


@router.get("/interviews", tags=["Recruiters"])
def interviews_list(params: Params = Depends()) -> Page[InterviewSchema]:
    with Session() as session:
        query = select(Interview)
        return paginate(session, query, params)


# UPDATE operations
@router.put("/recruiters/{id}", tags=["Recruiters"])
def recruiter_update(id: UUID, recruiter: RecruiterSchema):
    with Session() as session:
        # Update User table
        session.execute(
            update(User)
            .where(User.id == id)
            .values(
                first_name=recruiter.first_name,
                second_name=recruiter.second_name,
                last_name=recruiter.last_name,
                login=recruiter.login,
                password=recruiter.password,
                photo=recruiter.photo or None,
            )
        )
        # Update Recruiter table
        session.execute(
            update(Recruiter)
            .where(Recruiter.id == id)
            .values(department=recruiter.department)
        )
        session.commit()


@router.put("/vacancies/{id}", tags=["Recruiters"])
def vacancy_update(id: UUID, vacancy: VacancySchema):
    with Session() as session:
        session.execute(
            update(Vacancy)
            .where(Vacancy.id == id)
            .values(
                recruiter_id=vacancy.recruiter_id,
                description=vacancy.description,
                position=vacancy.position,
                keywords=vacancy.keywords,
                bucket_name=vacancy.bucket_name,
                filename=vacancy.filename,
                expires_at=vacancy.expires_at,
            )
        )
        session.commit()


@router.put("/interviews/{id}", tags=["Recruiters"])
def interview_update(id: UUID, interview: InterviewSchema):
    with Session() as session:
        session.execute(
            update(Interview)
            .where(Interview.id == id)
            .values(
                candidate_id=interview.candidate_id,
                vacancy_id=interview.vacancy_id,
                start_time=interview.start_time,
                report_json=interview.report_json,
                report_score=interview.report_score,
                verdict=interview.verdict,
                description=interview.description,
                conference_id=interview.conference_id,
            )
        )
        session.commit()


@router.post("/vacancies/{id}/upload_description", tags=["Recruiters"])
def vacancy_upload_description(id: UUID, file: UploadFile = File(...)):
    """
    Upload a description file for a vacancy to MinIO storage and update the vacancy's URL.
    """
    # MinIO configuration from populate.py
    client = Minio(
        "localhost:9000",
        access_key="root",
        secret_key="12345678",
        secure=False
    )

    bucket_name = "vacancies"

    # Generate unique filename
    file_extension = file.filename.split(
        '.')[-1] if '.' in file.filename else ''
    unique_filename = f"{id}_{uuid.uuid4().hex}.{file_extension}" if file_extension else f"{id}_{uuid.uuid4().hex}"

    try:
        # Ensure bucket exists
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        # Upload file to MinIO
        file_content = file.file.read()

        client.put_object(
            bucket_name,
            unique_filename,
            io.BytesIO(file_content),
            length=len(file_content)
        )

        # Update vacancy with bucket_name and filename in database
        with Session() as session:
            session.execute(
                update(Vacancy)
                .where(Vacancy.id == id)
                .values(bucket_name=bucket_name, filename=unique_filename)
            )
            session.commit()

        return {
            "message": "Description file uploaded successfully",
            "bucket_name": bucket_name,
            "filename": unique_filename
        }

    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
