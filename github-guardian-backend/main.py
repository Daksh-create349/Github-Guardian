from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.endpoints import scan, repo, webhook, desktop, auth
from src.db.session import engine
from src.db import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GitHub Guardian API")

@app.get("/")
async def root():
    return {"status": "GUARDIAN SYSTEM ONLINE", "message": "Forensic Security Audit Engine is operational."}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For initial beginner deployment. Re-tighten this after launch.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/api/v1")
app.include_router(repo.router, prefix="/api/v1")
app.include_router(webhook.router, prefix="/api/v1")
app.include_router(desktop.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
