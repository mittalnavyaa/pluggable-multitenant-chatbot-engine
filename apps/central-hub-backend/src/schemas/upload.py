from pydantic import BaseModel
from typing import List, Optional

class UploadResponse(BaseModel):
    job_id: str
    status: str

class TimelineItem(BaseModel):
    step: str
    label: str
    timestamp: str
    state: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: str
    estimated_time: str
    logs: List[str] = []
    timeline: List[TimelineItem] = []
    output_file: Optional[str] = None
    error_message: Optional[str] = None
