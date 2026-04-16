import os
import subprocess
import tempfile
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OR_API_KEY = os.getenv("OPENROUTER_API_KEY")
OR_MODEL = "google/gemini-2.0-flash-lite-001" # Verified OpenRouter slug

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OR_API_KEY,
)

def extract_raw_content(file_path: str) -> str:
    """Extracts text content, with special handling for .ipynb."""
    try:
        if file_path.endswith(".ipynb"):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                code_cells = [
                    "".join(cell.get("source", [])) 
                    for cell in data.get("cells", []) 
                    if cell.get("cell_type") == "code"
                ]
                return "\n\n".join(code_cells)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except:
        return ""

def generate_ai_code_review(owner: str, repo_name: str):
    """
    Genuine AI Architectural Review:
    - Extracts critical file snippets (including Jupyter Notebooks).
    - Sends them to OpenRouter for professional audit.
    """
    repo_url = f"https://github.com/{owner}/{repo_name}.git"
    critical_files = ["auth", "login", "db", "config", "server", "app", "controller", "middleware", "security", "routes", "train", "model", "predict"]
    source_exts = (".js", ".py", ".ts", ".go", ".java", ".php", ".c", ".cpp", ".ipynb", ".sh", ".yaml")

    review_summary = {
        "files_analyzed": [],
        "detailed_review": ""
    }

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, td], capture_output=True, check=False)
        
        all_files = []
        for root, _, fs in os.walk(td):
            for f in fs:
                rel_path = os.path.relpath(os.path.join(root, f), td)
                if any(x in rel_path for x in ["node_modules", ".git", "vendor", "venv", "__pycache__"]):
                    continue
                all_files.append(rel_path)

        # Select top 5 critical files
        selected_files = []
        for keyword in critical_files:
            for f in all_files:
                if keyword in f.lower() and f not in selected_files and f.endswith(source_exts):
                    selected_files.append(f)
                    if len(selected_files) >= 5: break
            if len(selected_files) >= 5: break

        if not selected_files:
            # Fallback: Just take any 3 source files
            selected_files = [f for f in all_files if f.endswith(source_exts)][:3]

        review_summary["files_analyzed"] = selected_files
        
        prompt_content = f"You are a professional security auditor. Perform a HIGH-LEVEL technical audit of the following files from {owner}/{repo_name}.\n\n"
        
        has_content = False
        for f in selected_files:
            file_path = os.path.join(td, f)
            content = extract_raw_content(file_path)
            if content.strip():
                has_content = True
                prompt_content += f"--- FILE: {f} ---\n"
                # Send first 150 lines/5000 chars
                prompt_content += content[:5000] + "\n\n"

        if not has_content:
             return {
                "files_analyzed": [],
                "detailed_review": "AI Review Skipped: No significant source code found for analysis (Check binary/asset-only repos)."
             }

        prompt_content += """
Based on the code snippets above, provide a CONCISE security review in Markdown format:
1. **Architectural Weaknesses**: Any structural risks (e.g., lack of middleware, improper error handling).
2. **Logic Flaws**: Vulnerabilities in sensitive flows (Auth, Session, Crypto).
3. **Actionable Remediation**: Specific steps to fix identified issues.

Keep it professional, technical, and objective.
"""

        if not OR_API_KEY:
            return {"detailed_review": "ERROR: OpenRouter API Key missing in environment."}

        try:
            # API Call to OpenRouter
            response = client.chat.completions.create(
                model=OR_MODEL,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=4000,
                extra_headers={
                    "HTTP-Referer": "https://github-guardian.local", # Optional
                    "X-Title": "GitHub Guardian Audit",
                }
            )
            
            review_summary["detailed_review"] = response.choices[0].message.content
            
        except Exception as e:
            review_summary["detailed_review"] = f"AI Review Failed: {str(e)}\n\nPlease ensure your OpenRouter API Key has sufficient credits."

    return review_summary
