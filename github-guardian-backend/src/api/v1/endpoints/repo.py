from fastapi import APIRouter
from src.services.github_client import github_client
import asyncio

router = APIRouter()

@router.get("/repo/{owner}/{repo_name}/overview")
async def get_overview(owner: str, repo_name: str):
    return await asyncio.to_thread(github_client.get_repo_overview, owner, repo_name)
