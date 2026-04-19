from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from typing import List, Optional
import asyncio

from src.services.github_desktop import (
    check_repo_name_availability,
    create_repo_and_push,
)
from src.api.v1.endpoints.auth import extract_github_token

router = APIRouter(prefix="/desktop", tags=["GitHub Desktop"])


def _get_user_token(authorization: Optional[str]) -> Optional[str]:
    """Extract the user's GitHub token from their JWT. Falls back to None (server token used)."""
    return extract_github_token(authorization) if authorization else None


@router.get("/check-name/{repo_name}")
async def check_name(repo_name: str, authorization: Optional[str] = Header(None)):
    """
    Check if a GitHub repository name is available.
    If the user is logged in (Authorization header), checks against their account.
    """
    try:
        user_token = _get_user_token(authorization)
        result = await asyncio.to_thread(
            check_repo_name_availability, repo_name, user_token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-and-push")
async def create_and_push_endpoint(
    repo_name: str = Form(...),
    description: str = Form(""),
    private: bool = Form(False),
    commit_message: str = Form("Initial commit"),
    files: List[UploadFile] = File(...),
    authorization: Optional[str] = Header(None),
):
    """
    Creates a GitHub repository and pushes all uploaded files.
    Uses the logged-in user's GitHub token if available.
    """
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(
            status_code=401,
            detail="You must be logged in with GitHub to create repositories."
        )

    try:
        file_data = []
        for f in files:
            content = await f.read()
            file_data.append((f.filename or "unnamed_file", content))

        result = await asyncio.to_thread(
            create_repo_and_push,
            repo_name=repo_name,
            description=description,
            private=private,
            commit_message=commit_message,
            files=file_data,
            github_token=user_token,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

