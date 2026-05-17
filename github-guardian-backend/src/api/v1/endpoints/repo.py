from fastapi import APIRouter, HTTPException
from src.services.github_client import github_client
import asyncio

router = APIRouter()

@router.get("/repo/{owner}/{repo_name}/overview")
async def get_overview(owner: str, repo_name: str):
    try:
        return await asyncio.to_thread(github_client.get_repo_overview, owner, repo_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
