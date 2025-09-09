# This file contains the WebSocket endpoint for AI-HR interviewer.
# It accepts WebSocket connections with interview_uuid and fetches interview data from external service.
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uuid import UUID
from minio import Minio
import io
from pipeline import ConferencePipeline
import logging
import json
import httpx
from analyzer import clean_and_format_dict, extract_text_as_single_line, parse_text_to_dict, parse_vacancy_from_json
import uvicorn


logger = logging.getLogger(__name__)

app = FastAPI()


class InterviewRequest(BaseModel):
    vacancy_uuid: UUID
    interview_uuid: UUID
    first_name: str
    last_name: str
    vacancy_bucket: str
    vacancy_filename: str
    resume_bucket: str
    resume_filename: str


class InterviewResult(BaseModel):
    interview_uuid: str
    analysis_result: str


async def fetch_interview_request(interview_id: UUID) -> InterviewRequest:
    """Fetch interview request data from external service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:9200/interview_requests/get/{interview_id}")
            response.raise_for_status()
            data = response.json()
            return InterviewRequest(**data)
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching interview request: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch interview request: {e}")
    except Exception as e:
        logger.error(f"Error fetching interview request: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching interview request: {e}")


async def extract_files_from_minio(vacancy_bucket: str, vacancy_filename: str,
                                   resume_bucket: str, resume_filename: str) -> tuple[str, str]:
    """Extract vacancy and resume files from MinIO storage and save to local directories using fget_object"""
    import os

    client = Minio("localhost:9000",
                   access_key="root",
                   secret_key="12345678",
                   secure=False)

    try:
        # Create directories if they don't exist
        os.makedirs("resources/vacancies", exist_ok=True)
        os.makedirs("resources/resumes", exist_ok=True)

        # Define local file paths
        vacancy_path = f"resources/vacancies/{vacancy_filename}"
        resume_path = f"resources/resumes/{resume_filename}"

        # Download vacancy file directly to local storage
        client.fget_object(vacancy_bucket, vacancy_filename, vacancy_path)

        # Download resume file directly to local storage
        client.fget_object(resume_bucket, resume_filename, resume_path)

        logger.info(f"Downloaded vacancy file to: {vacancy_path}")
        logger.info(f"Downloaded resume file to: {resume_path}")

        return vacancy_path, resume_path
    except Exception as e:
        logger.error(f"Error extracting files from MinIO: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error extracting files from MinIO: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        interview_uuid = websocket.query_params.get("interview_uuid")
        if not interview_uuid:
            await websocket.close()
            return

        # Fetch interview request data from external service
        logger.info(f"Fetching interview request for ID: {interview_uuid}")
        interview_request = await fetch_interview_request(UUID(interview_uuid))

        # Extract files from MinIO and save to local directories
        vacancy_path, resume_path = await extract_files_from_minio(
            interview_request.vacancy_bucket,
            interview_request.vacancy_filename,
            interview_request.resume_bucket,
            interview_request.resume_filename
        )

        # Extract vacancy text using analyzer function
        vacancy_text = extract_text_as_single_line(vacancy_path)
        vacancy_structured = parse_vacancy_from_json(
            clean_and_format_dict(
                parse_text_to_dict(vacancy_text)
            )
        )
        resume_text = extract_text_as_single_line(resume_path)

        # Create pipeline with vacancy text
        logger.info(
            f"Starting AI HR pipeline for candidate {interview_request.first_name} {interview_request.last_name}")
        pipeline = ConferencePipeline(vacancy_text=vacancy_text)

        # Run the blocking WebSocket pipeline
        await pipeline.process_websocket(websocket)

        # Analyze and store results when socket flow ends
        history_text = pipeline._format_dialog_history()
        try:
            analysis_result = pipeline.review.analyze_text(
                vacancy_text,
                history_text
            )
        except Exception as analyze_err:
            logger.error(f"Error during analysis: {analyze_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Error during analysis: {str(analyze_err)}"
            )

        # Create the result object
        result = InterviewResult(
            interview_uuid=interview_uuid,
            analysis_result=analysis_result
        )

        # Send the result to the external service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:9200/interviews/{interview_uuid}/assign_report",
                    json=result.dict()
                )
                response.raise_for_status()
                logger.info(
                    f"Successfully sent result to external service for interview {interview_uuid}")
        except Exception as send_err:
            logger.error(
                f"Failed to send result to external service: {send_err}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
        return
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}")
        try:
            await websocket.close()
        finally:
            return


async def main():
    config = uvicorn.Config("main:app", port=9300, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
