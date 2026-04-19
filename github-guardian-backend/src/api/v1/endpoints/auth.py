from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import RedirectResponse
from typing import Optional
import httpx
from jose import jwt, JWTError
from datetime import datetime, timedelta
from src.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


# ─── JWT Helpers ──────────────────────────────────────────────────────────────

def create_jwt(data: dict) -> str:
    payload = {
        **data,
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def extract_github_token(authorization: str) -> Optional[str]:
    """Helper: extract github_token from Bearer JWT header. Returns None if invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = decode_jwt(authorization.replace("Bearer ", ""))
        return payload.get("github_token")
    except JWTError:
        return None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/login")
def github_login():
    """
    Redirect the user to GitHub's OAuth authorization page.
    The browser should navigate HERE directly (not as an API call).
    """
    callback_url = f"{settings.backend_url}/api/v1/auth/callback"
    scope = "repo,user,delete_repo,read:org"
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope={scope}"
        f"&redirect_uri={callback_url}"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def github_callback(code: str):
    """
    GitHub redirects here after the user approves.
    We exchange the code for a token, wrap it in a JWT, and send the user back to the frontend.
    """
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=500,
            detail="OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env"
        )

    # Step 1: Exchange authorization code for a GitHub access token
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
        token_data = token_res.json()

    github_token = token_data.get("access_token")
    if not github_token:
        error = token_data.get("error_description", "Unknown error from GitHub")
        raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {error}")

    # Step 2: Fetch the user's GitHub profile
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_token}"},
            timeout=10,
        )
        user_info = user_res.json()

    # Step 3: Create a signed JWT containing the user's info + their GitHub token
    session_token = create_jwt({
        "github_token": github_token,
        "username": user_info.get("login"),
        "name": user_info.get("name") or user_info.get("login"),
        "avatar_url": user_info.get("avatar_url"),
        "email": user_info.get("email"),
    })

    # Step 4: Redirect back to the frontend with the JWT as a URL param
    frontend_callback = f"{settings.frontend_url}/auth/callback?token={session_token}"
    return RedirectResponse(frontend_callback)


@router.get("/me")
def get_current_user(authorization: str = Header(None)):
    """
    Returns the currently logged-in user's profile from their JWT.
    Frontend calls this on load to check if the user is already logged in.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_jwt(authorization.replace("Bearer ", ""))
        return {
            "username": payload.get("username"),
            "name": payload.get("name"),
            "avatar_url": payload.get("avatar_url"),
            "email": payload.get("email"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please log in again.")
