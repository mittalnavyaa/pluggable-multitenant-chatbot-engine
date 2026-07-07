from fastapi import APIRouter, UploadFile, File

from src.services.ingestion_service import (
    create_upload_job,
    get_job_status
)

from src.schemas.upload import (
    UploadResponse,
    StatusResponse
)

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    return create_upload_job(file)


@router.get(
    "/{job_id}/status",
    response_model=StatusResponse
)
async def document_status(
    job_id: str
):
    """
    Check upload status.
    """

    return get_job_status(job_id)