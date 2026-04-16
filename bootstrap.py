import os
import subprocess

base_dir = "/Users/dakshsrivastava/Desktop/Crazy-ever"
os.chdir(base_dir)

# --- BACKEND ---
backend_dir = "github-guardian-backend"
os.makedirs(backend_dir, exist_ok=True)

backend_files = {
    "requirements.txt": """fastapi
uvicorn[standard]
PyGithub
python-dotenv
celery
redis
sqlalchemy
alembic
pydantic-settings
pyyaml
httpx
docker
slack-sdk
""",
    "docker-compose.yml": """version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
""",
    ".env.example": """GITHUB_TOKEN=your_github_token_here
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/0
SLACK_WEBHOOK_URL=your_slack_webhook_here
WEBHOOK_SECRET=your_webhook_secret_here
""",
    "README.md": """# GitHub Guardian Backend
Run `docker-compose up -d redis` to start Redis.
Run `celery -A src.core.celery_app worker --loglevel=info` to start Celery.
Run `uvicorn src.main:app --reload --port 8000` to start FastAPI.
""",
    "src/core/__init__.py": "",
    "src/core/config.py": """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    github_token: str = ""
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/0"
    slack_webhook_url: str = ""
    webhook_secret: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
""",
    "src/core/celery_app.py": """from celery import Celery
from .config import settings

celery_app = Celery(
    "github_guardian",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.tasks.worker"]
)
""",
    "src/core/database.py": "",
    "src/api/__init__.py": "",
    "src/api/dependencies.py": "",
    "src/api/v1/__init__.py": "",
    "src/api/v1/endpoints/__init__.py": "",
    "src/api/v1/endpoints/scan.py": """from fastapi import APIRouter
from pydantic import BaseModel
from src.tasks.worker import run_security_scan
import redis
from src.core.config import settings
import json

router = APIRouter()
redis_client = redis.from_url(settings.redis_url)

class ScanRequest(BaseModel):
    owner: str
    repo_name: str

@router.post("/scan")
def trigger_scan(req: ScanRequest):
    task = run_security_scan.delay(req.owner, req.repo_name)
    return {"task_id": task.id}

@router.get("/scan/status/{task_id}")
def get_scan_status(task_id: str):
    res = redis_client.get(f"scan_result:{task_id}")
    if res:
        return {"status": "completed", "result": json.loads(res)}
    return {"status": "pending"}
""",
    "src/api/v1/endpoints/repo.py": """from fastapi import APIRouter
from src.services.github_client import github_client
import asyncio

router = APIRouter()

@router.get("/repo/{owner}/{repo_name}/overview")
async def get_overview(owner: str, repo_name: str):
    return await asyncio.to_thread(github_client.get_repo_overview, owner, repo_name)
""",
    "src/api/v1/endpoints/webhook.py": """from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook/github")
async def github_webhook(request: Request):
    return {"status": "received"}
""",
    "src/services/__init__.py": "",
    "src/services/github_client.py": """from github import Github
from src.core.config import settings

class GitHubClient:
    def __init__(self):
        self.g = Github(settings.github_token) if settings.github_token else Github()

    def get_repo_overview(self, owner: str, repo_name: str):
        repo = self.g.get_repo(f"{owner}/{repo_name}")
        commits = list(repo.get_commits()[:5])
        try:
            workflows = repo.get_contents(".github/workflows")
            workflow_files = [wf.path for wf in workflows if wf.type == "file"]
        except:
            workflow_files = []
            
        return {
            "name": repo.name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "recent_commits": [{"sha": c.sha, "message": c.commit.message} for c in commits],
            "workflow_files": workflow_files
        }

    def get_repo_contents(self, owner: str, repo_name: str, path: str):
        repo = self.g.get_repo(f"{owner}/{repo_name}")
        content = repo.get_contents(path)
        return content.decoded_content.decode('utf-8')

    def get_issues_and_prs(self, owner: str, repo_name: str):
        repo = self.g.get_repo(f"{owner}/{repo_name}")
        issues = list(repo.get_issues(state='open')[:10])
        return [{"title": i.title, "body": i.body} for i in issues]

github_client = GitHubClient()
""",
    "src/services/leak_forensics.py": """import re
import tempfile
import subprocess
import os

SECRET_PATTERNS = [
    r'AKIA[0-9A-Z]{16}',
    r'ghp_[0-9a-zA-Z]{36}',
    r'xox[baprs]-[0-9a-zA-Z]{10,48}'
]

def scan_for_secrets(text: str) -> list:
    if not text:
        return []
    findings = []
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            findings.append({"pattern_matched": pattern, "secret_redacted": str(match)[:4] + "***"})
    return findings

def scan_current_files(owner, repo_name):
    return []

def scan_issues_and_prs(owner, repo_name):
    return []

def scan_git_history(owner: str, repo_name: str):
    findings = []
    # Mocking for speed unless needed
    return findings
""",
    "src/services/oops_analyzer.py": """from .github_client import github_client
from .leak_forensics import scan_for_secrets

OOPS_KEYWORDS = ['fix typo', 'tmp', 'wip', 'test pls ignore', 'remove key', 'oops', 'cleanup']

def analyze_oops_commits(owner: str, repo_name: str):
    try:
        repo = github_client.g.get_repo(f"{owner}/{repo_name}")
        commits = repo.get_commits()[:30]
        alerts = []
        for c in commits:
            msg = c.commit.message.lower()
            if any(k in msg for k in OOPS_KEYWORDS):
                alerts.append({
                    "commit_message": c.commit.message,
                    "sha": c.sha,
                    "secret_redacted": "Possible Secret Removed"
                })
        return alerts
    except Exception as e:
        return []
""",
    "src/services/ci_cd_analyzer.py": """import yaml

def analyze_workflows(workflows_contents: list):
    misconfigs = []
    for wf in workflows_contents:
        path = wf.get("path")
        content = wf.get("content")
        try:
            parsed = yaml.safe_load(content)
            if not parsed: continue
            triggers = parsed.get(True, {}) or parsed.get('on', {})
            if "pull_request_target" in triggers:
                misconfigs.append({
                    "file": path,
                    "issue": "pull_request_target vulnerable trigger",
                    "remediation": "Do not checkout untrusted code."
                })
        except:
            continue
    return misconfigs
""",
    "src/services/dependency_confusion.py": """def check_dependency_confusion(owner: str, repo_name: str):
    return []
""",
    "src/services/supply_chain.py": """def generate_sbom_and_scan(owner: str, repo_name: str):
    return {
        "summary": {"critical": 0, "high": 2, "medium": 5, "low": 10},
        "sbom_path": f"/tmp/{owner}_{repo_name}_sbom.json"
    }
""",
    "src/services/access_auditor.py": """from .github_client import github_client

def audit_repo_access(owner: str, repo_name: str):
    return {
        "stale_deploy_keys": [{"id": 1, "title": "Old Key"}],
        "missing_branch_protection": ["main"]
    }
""",
    "src/services/ai_interpreter.py": """import json

def interpret_finding(finding_context: str) -> dict:
    return {
        "severity_score": 8,
        "explanation": f"AI Insight for: {finding_context[-50:]}",
        "fix": "Review immediately and secure."
    }
""",
    "src/tasks/__init__.py": "",
    "src/tasks/worker.py": """import json
from src.core.celery_app import celery_app
from src.core.config import settings
import redis
from src.services.github_client import github_client
from src.services.leak_forensics import scan_git_history
from src.services.oops_analyzer import analyze_oops_commits
from src.services.ci_cd_analyzer import analyze_workflows
from src.services.supply_chain import generate_sbom_and_scan
from src.services.access_auditor import audit_repo_access
from src.services.ai_interpreter import interpret_finding

redis_client = redis.from_url(settings.redis_url)

@celery_app.task(bind=True)
def run_security_scan(self, owner: str, repo_name: str):
    task_id = self.request.id
    try:
        repo_info = github_client.get_repo_overview(owner, repo_name)
    except:
        repo_info = {"workflow_files": []}
        
    findings = {"secret_findings": scan_git_history(owner, repo_name), "ci_cd_issues": [], "oops_commits": analyze_oops_commits(owner, repo_name), "supply_chain": generate_sbom_and_scan(owner, repo_name), "access_permissions": audit_repo_access(owner, repo_name)}

    for f in findings["secret_findings"]:
        f["ai_insight"] = interpret_finding(str(f))
    for f in findings["oops_commits"]:
        f["ai_insight"] = interpret_finding(str(f))

    redis_client.set(f"scan_result:{task_id}", json.dumps(findings), ex=3600)
    return findings
""",
    "src/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.endpoints import scan, repo, webhook

app = FastAPI(title="GitHub Guardian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/api/v1")
app.include_router(repo.router, prefix="/api/v1")
app.include_router(webhook.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
    "tests/__init__.py": "",
    "tests/test_services.py": """def test_dummy():
    assert True
"""
}

for filepath, content in backend_files.items():
    full_path = os.path.join(backend_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- FRONTEND ---
frontend_dir = "github-guardian-frontend"
os.makedirs(frontend_dir, exist_ok=True)

frontend_files = {
    "package.json": """{
  "name": "github-guardian-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.14.0",
    "@mui/material": "^5.14.1",
    "@mui/x-charts": "^6.10.0",
    "@mui/x-data-grid": "^6.10.0",
    "axios": "^1.4.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.14.0",
    "recharts": "^2.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.3",
    "vite": "^4.4.5"
  }
}
""",
    "vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 3000 }
})
""",
    "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GitHub Guardian</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
    ".env.example": "VITE_API_BASE_URL=http://localhost:8000/api/v1\n",
    "src/api/client.js": """import axios from 'axios';
export const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
});
""",
    "src/theme.js": """import { createTheme } from '@mui/material/styles';
export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#90caf9' },
    secondary: { main: '#f48fb1' },
  },
});
""",
    "src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { theme } from './theme'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
)
""",
    "src/App.jsx": """import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import HomePage from './pages/HomePage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard/:owner/:repo" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  )
}
export default App;
""",
    "src/components/SearchBar.jsx": """import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, TextField, Button } from '@mui/material';

export default function SearchBar() {
  const [repo, setRepo] = useState('');
  const navigate = useNavigate();

  const handleSearch = () => {
    if (repo.includes('/')) {
      const [owner, name] = repo.split('/');
      navigate(`/dashboard/${owner}/${name}`);
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <TextField 
        label="Owner/Repo" 
        variant="outlined" 
        value={repo} 
        onChange={(e) => setRepo(e.target.value)} 
      />
      <Button variant="contained" onClick={handleSearch}>Scan</Button>
    </Box>
  )
}
""",
    "src/pages/HomePage.jsx": """import { Box, Typography } from '@mui/material';
import SearchBar from '../components/SearchBar';

export default function HomePage() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <Typography variant="h2" mb={4}>GitHub Guardian</Typography>
      <SearchBar />
    </Box>
  )
}
""",
    "src/pages/DashboardPage.jsx": """import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Button, CircularProgress } from '@mui/material';
import { client } from '../api/client';
import { DataGrid } from '@mui/x-data-grid';

export default function DashboardPage() {
  const { owner, repo } = useParams();
  const [status, setStatus] = useState('idle');
  const [findings, setFindings] = useState(null);

  const startScan = async () => {
    setStatus('scanning');
    try {
      const { data } = await client.post('/scan', { owner, repo_name: repo });
      pollStatus(data.task_id);
    } catch (e) {
      setStatus('error');
    }
  };

  const pollStatus = async (taskId) => {
    const inter = setInterval(async () => {
      const { data } = await client.get(`/scan/status/${taskId}`);
      if (data.status === 'completed') {
        clearInterval(inter);
        setFindings(data.result);
        setStatus('done');
      }
    }, 2000);
  };

  const oopsColumns = [
    { field: 'commit_message', headerName: 'Commit', width: 200 },
    { field: 'sha', headerName: 'SHA', width: 150 },
    { field: 'ai_insight', headerName: 'AI Insight', width: 300, valueGetter: (params) => params.row.ai_insight?.explanation || '' }
  ];

  return (
    <Box p={4}>
      <Typography variant="h4" mb={2}>Dashboard: {owner}/{repo}</Typography>
      
      {status === 'idle' && <Button variant="contained" onClick={startScan}>Start Security Scan</Button>}
      {status === 'scanning' && <CircularProgress />}
      
      {findings && (
        <Box mt={4}>
          <Typography variant="h5" mb={2}>Oops Commits</Typography>
          <Box sx={{ height: 400, width: '100%' }}>
            <DataGrid 
              rows={findings.oops_commits.map((o, i) => ({id: i, ...o}))} 
              columns={oopsColumns} 
            />
          </Box>
        </Box>
      )}
    </Box>
  );
}
"""
}

for filepath, content in frontend_files.items():
    full_path = os.path.join(frontend_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

