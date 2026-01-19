from fastapi import APIRouter, Depends
from dependencies import verify_api_key
from pydantic import BaseModel

# 1. Define your schema
class JobRequest(BaseModel):
    task: str

# 2. Use APIRouter instead of app
router = APIRouter()

@router.post("/spawn_agent")
async def run_agent_job(job: JobRequest, user_info: tuple = Depends(verify_api_key)):
    user_id, plan = user_info
    
    # To avoid circular imports, import the instance inside the function
    from main import os_instance 
    
    final_output = os_instance.app.invoke({"task": job.task})
    return {"status": "success", "trace": final_output}