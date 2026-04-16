from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook/github")
async def github_webhook(request: Request):
    return {"status": "received"}
