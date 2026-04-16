from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from src.tasks.worker import run_security_scan
from src.core.database import scan_storage
import uuid

router = APIRouter()

class ScanRequest(BaseModel):
    owner: str
    repo_name: str

@router.post("/scan")
async def trigger_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    # Queue the work natively without Redis/Celery
    background_tasks.add_task(run_security_scan, task_id, req.owner, req.repo_name)
    return {"task_id": task_id}

@router.get("/scan/status/{task_id}")
async def get_scan_status(task_id: str):
    data = scan_storage.get(task_id)
    if data:
        return data
    return {"status": "pending"}
