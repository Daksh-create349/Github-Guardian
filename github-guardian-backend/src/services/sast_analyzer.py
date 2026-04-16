import os
import re
import subprocess
import tempfile

# Professional SAST Patterns (Semantic Security)
SAST_PATTERNS = [
    {
        "id": "SQLI_RAW_QUERY",
        "name": "Potential SQL Injection (Raw Query)",
        "patterns": [
            r"\.execute\(\".*%\s*\"", # Python/JS style % interpolation
            r"\.query\(\".*\$\{.*\}\"\)", # JS Template Literals in query
            r"SELECT .* FROM .* WHERE .* \+ .*", # Basic string concat
        ],
        "languages": [".py", ".js", ".ts", ".java", ".php"],
        "severity": "CRITICAL"
    },
    {
        "id": "XSS_DANGEROUS_RENDER",
        "name": "Cross-Site Scripting (Insecure Rendering)",
        "patterns": [
            r"dangerouslySetInnerHTML", # React
            r"\.innerHTML\s*=", # Vanilla JS
            r"\{\{\s*.*\s*\|\s*safe\s*\}\}", # Jinja/Nunjucks 'safe' filter
        ],
        "languages": [".js", ".jsx", ".ts", ".tsx", ".html"],
        "severity": "HIGH"
    },
    {
        "id": "INSECURE_SUBPROCESS",
        "name": "Insecure Process Execution (Shell Injection)",
        "patterns": [
            r"shell=True", # Python
            r"child_process\.exec\(", # Node.js
            r"system\(.*\+.*\)", # C/PHP style
        ],
        "languages": [".py", ".js", ".c", ".php"],
        "severity": "HIGH"
    },
    {
        "id": "HARDCODED_AUTH",
        "name": "Hardcoded Authentication/Token",
        "patterns": [
            r"password\s*=\s*['\"][^'\"]+['\"]", # Common password assignment
            r"JWT_SECRET\s*=\s*['\"][^'\"]+['\"]",
        ],
        "languages": [".py", ".js", ".ts", ".env"],
        "severity": "CRITICAL"
    }
]

def analyze_code_semantics(owner: str, repo_name: str):
    findings = []
    repo_url = f"https://github.com/{owner}/{repo_name}.git"
    
    with tempfile.TemporaryDirectory() as td:
        # Clone repo
        subprocess.run(["git", "clone", "--depth", "1", repo_url, td], capture_output=True, check=False)
        
        # Get list of files
        ls_res = subprocess.run(["git", "-C", td, "ls-files"], capture_output=True, text=True, check=False)
        if not ls_res.stdout:
            return []

        files = ls_res.stdout.splitlines()
        
        for file_path in files:
            ext = os.path.splitext(file_path)[1]
            full_path = os.path.join(td, file_path)
            
            # Skip binary files/heavy files
            if ext in [".png", ".jpg", ".pdf", ".zip"]: continue
            
            try:
                with open(full_path, 'r', errors='ignore') as f:
                    content = f.read()
                    
                for rule in SAST_PATTERNS:
                    if ext in rule["languages"] or not rule["languages"]:
                        for pattern in rule["patterns"]:
                            if re.search(pattern, content):
                                findings.append({
                                    "type": rule["name"],
                                    "file": file_path,
                                    "severity": rule["severity"],
                                    "pattern_matched": pattern
                                })
                                break # One finding per rule per file
            except: continue
            
    return findings
