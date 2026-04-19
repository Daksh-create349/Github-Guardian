from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio

from src.db.session import get_db
from src.db.models import PushHistory
from src.services.github_desktop import (
    check_repo_name_availability,
    create_repo_and_push,
    smart_push_to_existing_repo,
    create_new_branch,
    push_files_to_branch,
    merge_with_conflict_check,
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


@router.post("/smart-push")
async def smart_push_endpoint(
    repo_name: str = Form(...),
    commit_message: str = Form("Auto update from GitHub Guardian"),
    files: List[UploadFile] = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Intelligently pushes files to an EXISTING repository.
    Handles branch creation, AI conflict resolution, PR generation, and auto-merging.
    """
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="You must be logged in with GitHub.")

    # Try to extract username from token for DB tracking
    # (Typically would just decode JWT but we can fetch it via Github in the smart_push logic or pass it. 
    # For now, let's extract username directly if we can, or just save generic)
    from src.api.v1.endpoints.auth import decode_jwt
    username = "unknown"
    try:
        payload = decode_jwt(authorization.replace("Bearer ", ""))
        username = payload.get("username", "unknown")
    except:
        pass

    try:
        file_data = []
        for f in files:
            content = await f.read()
            file_data.append((f.filename or "unnamed_file", content))

        result = await smart_push_to_existing_repo(
            repo_name=repo_name,
            commit_message=commit_message,
            files=file_data,
            github_token=user_token,
        )

        # Log to Database
        db_entry = PushHistory(
            github_username=username,
            repository_name=repo_name,
            branch_name="guardian-update-*",  # We can be generic or extract from result if we want
            commit_message=commit_message,
            status="auto_merged" if result.get("merged") else "pr_created",
            log_details=str(result)
        )
        db.add(db_entry)
        db.commit()

        return result

    except Exception as e:
        # Log failure
        db_entry = PushHistory(
            github_username=username,
            repository_name=repo_name,
            branch_name="guardian-update-*",
            commit_message=commit_message,
            status="error",
            log_details=str(e)
        )
        db.add(db_entry)
        db.commit()
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_push_history(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Fetch push history for the logged in user
    """
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    from src.api.v1.endpoints.auth import decode_jwt
    try:
        payload = decode_jwt(authorization.replace("Bearer ", ""))
        username = payload.get("username")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    history = db.query(PushHistory).filter(PushHistory.github_username == username).order_by(PushHistory.created_at.desc()).all()
    return history


@router.get("/github-repos")
async def get_github_repos(
    authorization: Optional[str] = Header(None),
):
    """
    Fetch all real GitHub repositories for the logged in user directly from GitHub API.
    Returns a list of repos with name, description, last push time, visibility, URL.
    """
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        from github import Github
        g = Github(user_token)
        user = g.get_user()
        repos = user.get_repos(sort="pushed", direction="desc")

        result = []
        for repo in repos:
            result.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "",
                "private": repo.private,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "default_branch": repo.default_branch,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "language": repo.language or "Unknown",
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "open_issues_count": repo.open_issues_count,
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/branches/{repo_name}")
async def get_repo_branches(
    repo_name: str,
    authorization: Optional[str] = Header(None),
):
    """
    Fetch all branches for a specific repository.
    Returns branch name, last commit message, author, and date.
    """
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        from github import Github
        g = Github(user_token)
        user = g.get_user()
        repo = user.get_repo(repo_name)

        branches = []
        for branch in repo.get_branches():
            commit = branch.commit.commit
            branches.append({
                "name": branch.name,
                "is_default": branch.name == repo.default_branch,
                "last_commit_message": commit.message.split("\n")[0],
                "last_commit_author": commit.author.name if commit.author else "Unknown",
                "last_commit_date": commit.author.date.isoformat() if commit.author else None,
                "sha": branch.commit.sha,
            })

        # Sort: default branch first, then alphabetical
        branches.sort(key=lambda b: (not b["is_default"], b["name"]))

        return {
            "repo_name": repo.name,
            "full_name": repo.full_name,
            "html_url": repo.html_url,
            "default_branch": repo.default_branch,
            "description": repo.description or "",
            "private": repo.private,
            "branches": branches,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/branch-push")
async def branch_push_endpoint(
    repo_name: str = Form(...),
    target_branch: str = Form(...),
    commit_message: str = Form("Update via GitHub Guardian"),
    files: List[UploadFile] = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Push files to a SPECIFIC branch of an existing repository.
    Creates a new guardian-update branch from the target, resolves conflicts via AI,
    opens a PR targeting the specified branch, and auto-merges it.
    """
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="You must be logged in with GitHub.")

    from src.api.v1.endpoints.auth import decode_jwt
    username = "unknown"
    try:
        payload = decode_jwt(authorization.replace("Bearer ", ""))
        username = payload.get("username", "unknown")
    except:
        pass

    try:
        file_data = []
        for f in files:
            content = await f.read()
            file_data.append((f.filename or "unnamed_file", content))

        result = await smart_push_to_existing_repo(
            repo_name=repo_name,
            commit_message=commit_message,
            files=file_data,
            github_token=user_token,
        )

        db_entry = PushHistory(
            github_username=username,
            repository_name=repo_name,
            branch_name=target_branch,
            commit_message=commit_message,
            status="auto_merged" if result.get("merged") else "pr_created",
            log_details=str(result)
        )
        db.add(db_entry)
        db.commit()

        return result

    except Exception as e:
        db_entry = PushHistory(
            github_username=username,
            repository_name=repo_name,
            branch_name=target_branch,
            commit_message=commit_message,
            status="error",
            log_details=str(e)
        )
        db.add(db_entry)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-branch")
async def create_branch_endpoint(
    repo_name: str = Form(...),
    new_branch_name: str = Form(...),
    base_branch: str = Form(...),
    authorization: Optional[str] = Header(None),
):
    """Create a new branch off a base branch in a repo."""
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        result = await asyncio.to_thread(
            create_new_branch, repo_name, new_branch_name, base_branch, user_token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/push-to-branch")
async def push_to_branch_endpoint(
    repo_name: str = Form(...),
    branch_name: str = Form(...),
    commit_message: str = Form(""),
    files: List[UploadFile] = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Push files directly to a specific branch (no PR, no merge)."""
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    from src.api.v1.endpoints.auth import decode_jwt
    username = "unknown"
    try:
        payload = decode_jwt(authorization.replace("Bearer ", ""))
        username = payload.get("username", "unknown")
    except:
        pass

    try:
        file_data = [(f.filename or "unnamed", await f.read()) for f in files]
        result = await asyncio.to_thread(
            push_files_to_branch, repo_name, branch_name, commit_message, file_data, user_token
        )
        db.add(PushHistory(
            github_username=username, repository_name=repo_name,
            branch_name=branch_name, commit_message=commit_message,
            status="pushed_to_branch", log_details=str(result)
        ))
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge-branch")
async def merge_branch_endpoint(
    repo_name: str = Form(...),
    source_branch: str = Form(...),
    target_branch: str = Form(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Check conflicts, AI-resolve if possible, create PR and merge."""
    user_token = _get_user_token(authorization)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    from src.api.v1.endpoints.auth import decode_jwt
    username = "unknown"
    try:
        payload = decode_jwt(authorization.replace("Bearer ", ""))
        username = payload.get("username", "unknown")
    except:
        pass

    try:
        result = await merge_with_conflict_check(repo_name, source_branch, target_branch, user_token)
        status = "auto_merged" if result.get("merged") else (
            "conflict_unfixable" if result.get("reason") == "conflict_unfixable" else "merge_failed"
        )
        db.add(PushHistory(
            github_username=username, repository_name=repo_name,
            branch_name=f"{source_branch} → {target_branch}",
            commit_message=f"Merge '{source_branch}' into '{target_branch}'",
            status=status, log_details=str(result)
        ))
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
