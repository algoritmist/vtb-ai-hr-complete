import io
from uuid import UUID
import uuid

from fastapi import HTTPException, Depends, UploadFile, File
from fastapi_pagination import Page, Params
from candidate.schemas import CandidateSchema
from database import Session
from sqlalchemy import insert, update, select
from minio import Minio
from minio.error import S3Error

from .models import Candidate
from common.models import User

from .router import router

from fastapi_pagination.ext.sqlalchemy import paginate


@router.post("/candidates/create", status_code=201, tags=["Users"])
def candidate_create(candidate: CandidateSchema):
    with Session() as session:
        query1 = (
            insert(User)
            .values(
                first_name=candidate.first_name,
                second_name=candidate.second_name,
                last_name=candidate.last_name,
                login=candidate.login,
                password=candidate.password,
                photo=candidate.photo,
            )
            .returning(User.id)
        )
        result1 = session.execute(query1)
        user_id = result1.scalar()
        query2 = insert(Candidate).values(id=user_id, resume=candidate.resume)
        session.execute(query2)
        session.commit()
        return user_id


@router.get("/candidates/{id}", tags=["Users"])
def candidate_get(id: UUID) -> CandidateSchema:
    with Session() as session:
        result = session.execute(
            select(Candidate, User)
            .join(User, Candidate.id == User.id)
            .where(Candidate.id == id)
        )
        candidate_data, user_data = result.first()
        if not candidate_data:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return CandidateSchema(
            id=user_data.id,
            first_name=user_data.first_name,
            second_name=user_data.second_name,
            last_name=user_data.last_name,
            login=user_data.login,
            photo=user_data.photo,
            resume=candidate_data.resume
        )


# LIST operation with pagination
@router.get("/candidates", tags=["Users"])
def candidates_list(params: Params = Depends()) -> Page[CandidateSchema]:
    with Session() as session:
        query = select(User, Candidate).join(
            Candidate, Candidate.id == User.id)

        def transformer(items):
            return [
                CandidateSchema(
                    id=user.id,
                    first_name=user.first_name,
                    second_name=user.second_name,
                    last_name=user.last_name,
                    login=user.login,
                    photo=user.photo,
                    resume=candidate.resume
                )
                for user, candidate in items
            ]

        return paginate(session, query, params, transformer=transformer)


# UPDATE operation
@router.put("/candidates/{id}", tags=["Users"])
def candidate_update(id: UUID, candidate: CandidateSchema):
    with Session() as session:
        # Update User table
        session.execute(
            update(User)
            .where(User.id == id)
            .values(
                first_name=candidate.first_name,
                second_name=candidate.second_name,
                last_name=candidate.last_name,
                login=candidate.login,
                password=candidate.password,
                photo=candidate.photo or None,
            )
        )
        # Update Candidate table
        session.execute(
            update(Candidate)
            .where(Candidate.id == id)
            .values(resume=candidate.resume)
        )
        session.commit()


@router.post("/candidates/{id}/upload_photo", tags=["Users"])
def candidate_upload_photo(id: UUID, photo: UploadFile = File(...)):
    """
    Upload a photo for a candidate to MinIO storage and update the candidate's photo.
    """
    # MinIO configuration from populate.py
    client = Minio(
        "localhost:9000",
        access_key="root",
        secret_key="12345678",
        secure=False
    )

    bucket_name = "photos"

    # Generate unique filename
    file_extension = photo.filename.split(
        '.')[-1] if '.' in photo.filename else ''
    unique_filename = f"{id}_{uuid.uuid4().hex}.{file_extension}" if file_extension else f"{id}_{uuid.uuid4().hex}"

    try:
        # Ensure bucket exists
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        # Upload file to MinIO
        file_content = photo.file.read()
        client.put_object(
            bucket_name,
            unique_filename,
            io.BytesIO(file_content),
            length=len(file_content)
        )

        # Update candidate photo in database
        with Session() as session:
            session.execute(
                update(User).where(User.id == id).values(photo=unique_filename)
            )
            session.commit()

        return {
            "message": "Photo uploaded successfully",
            "bucket_name": bucket_name,
            "filename": unique_filename
        }

    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/candidates/{id}/upload_resume", tags=["Users"])
def candidate_upload_resume(id: UUID, resume: UploadFile = File(...)):
    """
    Upload a resume for a candidate to MinIO storage and update the candidate's resume.
    """
    # MinIO configuration from populate.py
    client = Minio(
        "localhost:9000",
        access_key="root",
        secret_key="12345678",
        secure=False
    )

    bucket_name = "resume"

    # Generate unique filename
    file_extension = resume.filename.split(
        '.')[-1] if '.' in resume.filename else ''
    unique_filename = f"{id}_{uuid.uuid4().hex}.{file_extension}" if file_extension else f"{id}_{uuid.uuid4().hex}"

    try:
        # Ensure bucket exists
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        # Upload file to MinIO
        file_content = resume.file.read()
        client.put_object(
            bucket_name,
            unique_filename,
            io.BytesIO(file_content),
            length=len(file_content)
        )

        # Update candidate resume in database
        with Session() as session:
            session.execute(
                update(Candidate).where(Candidate.id ==
                                        id).values(resume=unique_filename)
            )
            session.commit()

        return {
            "message": "Resume uploaded successfully",
            "bucket_name": bucket_name,
            "filename": unique_filename
        }

    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
