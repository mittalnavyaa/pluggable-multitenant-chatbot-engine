import uuid
from src.services.storage_service import upload_file

def create_upload_job(file):
    object_name = upload_file(file)

    return {
        "job_id": str(uuid.uuid4()),
        "status": "UPLOADING",
        "object_name": object_name
    }


def get_job_status(job_id: str):
    return {
        "job_id": job_id,
        "status": "QUEUED"
    }