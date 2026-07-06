import uuid


def create_upload_job():
    job_id = str(uuid.uuid4())

    return {
        "job_id": job_id,
        "status": "QUEUED"
    }


def get_job_status(job_id: str):
    return {
        "job_id": job_id,
        "status": "QUEUED"
    }