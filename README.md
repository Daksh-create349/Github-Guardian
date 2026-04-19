<div align="center">
  <img src="https://raw.githubusercontent.com/github/explore/80688e429a7d4ef2fca1e82350fe8e3517d3494d/topics/security/security.png" alt="Security Shield" width="120" />
  <br/>
  <h1>GitHub Guardian</h1>
  <p><strong>Deep Forensic Security & Safe Repository Management for the Modern Developer</strong></p>

  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
  [![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org/)
  [![GitHub OAuth](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](#)
  [![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](#)

</div>

---

## ⚡ Introduction

GitHub Guardian is an advanced, high-fidelity security auditing platform built to solve the "signal-to-noise" problem in modern DevSecOps. Traditional scanners flood developers with low-priority warnings. Guardian focuses strictly on **Forensic Impact**—hunting active secrets, detecting structural flaws, and verifying supply chain integrity.

Now featuring an integrated **GitHub Desktop interface**, the platform allows developers to create secure repositories, automatically protect secrets through generated `.gitignore` files, and push code directly from the browser natively through their GitHub accounts.

---

## 🚀 Key Features

### 1. The GitHub Desktop Wizard
A smooth, retro-styled web interface for securely initializing GitHub repositories.
- **OAuth Integration**: Securely log in with GitHub to push code to your personal or organizational account.
- **Smart Drag & Drop**: Add your project files instantly through the browser.
- **Auto-Protect Secrets**: Automatically scans for `.env` files, `.pem` keys, and `node_modules` and dynamically generates a bulletproof `.gitignore` to prevent massive leaks.
- **One-Click Push**: Instantly creates the remote repo, commits your code, and pushes the initial branch.

### 2. Deep Forensic Auditing (SAST & History)
- **Live Exposure Detection**: Hunts the current codebase for active API keys, SSL certificates, and sensitive credentials.
- **"OOPS Commit" Forensics**: Traverses the Git DAG (Directed Acyclic Graph) to find deleted secrets that still remain buried in historical blobs.
- **Semantic Code Scanning**: Identifies real-world vulnerabilities (raw SQL injection, dangerous `eval` execution, XSS paths).

### 3. AI Architectural Reviewer
Powered by state-of-the-art LLMs (OpenAI/Gemini integrations).
- Conducts subjective architectural analysis.
- Extracts "Critical Path" files (Auth, DB, Routing).
- Fully supports Data Science repositories by parsing `.ipynb` Jupyter notebook cells.

---

## 📐 The Architecture

- **Backend**: **FastAPI** drives an asynchronous orchestration pipeline. It utilizes `PyGithub` for tree/blob manipulation, `python-jose` for JWT sessions, and interfaces securely with AI endpoints.
- **Frontend**: **React + Vite** delivering a stunning "Neo-Retro" 8-bit interface. Customized Material UI components wrapped in VT323 typography create an authoritative "mainframe terminal" experience.
- **Scoring Engine**: Implements a non-linear normalization curve (`Final Score = 10 * (1 - 0.85^(raw_score / 2))`) to prevent alert fatigue, keeping a 10/10 score reserved only for total security collapses.

---

## 🛠️ Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/github-guardian.git
cd github-guardian
```

### 2. Backend Setup
```bash
cd github-guardian-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Create a `.env` file containing your credentials:
```env
GITHUB_TOKEN=your_fallback_server_token
GITHUB_CLIENT_ID=your_oauth_client_id
GITHUB_CLIENT_SECRET=your_oauth_client_secret
JWT_SECRET=your_super_secret_jwt_key
OPENAI_API_KEY=your_openai_key

FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```
Start the API:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd github-guardian-frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000` to begin your deep forensic audit!

---

## 🧪 Testing the Auditor

Want to test GitHub Guardian's forensic capabilities? Try scanning these intentionally vulnerable repositories:
- [OWASP NodeGoat](https://github.com/OWASP/NodeGoat) - Demonstrates high-risk vulnerabilities in Node.js applications.
- [Broken Crystals](https://github.com/BrightSecurity/broken-crystals) - A modern vulnerable application featuring complex SAST and secret-based vulnerabilities.

---

> *"Security isn't about building a wall. It's about knowing exactly what's inside the walls."*
