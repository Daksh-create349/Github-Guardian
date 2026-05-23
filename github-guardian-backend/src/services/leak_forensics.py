import re
import tempfile
import subprocess
import os
import math

# Robust set of enterprise-grade patterns (parity with CLI)
SECRET_PATTERNS = {
    "AWS Access Key ID": r'AKIA[0-9A-Z]{16}',
    "AWS Secret Key": r'(?i)aws_secret_access_key\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
    "GitHub Token": r'gh[pousr]_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z]{82}',
    "Slack Webhook": r'https://hooks\.slack\.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}/[0-9a-zA-Z]{24}',
    "Slack Token": r'xox[bapr]-[0-9a-zA-Z]{10,48}',
    "Stripe API Key": r'[rs]k_(?:live|test)_[0-9a-zA-Z]{24,32}',
    "Google API Key": r'AIza[0-9A-Za-z\-_]{35}',
    "OpenAI API Key": r'sk-[a-zA-Z0-9]{20,}|sk\s*-\s*[a-zA-Z0-9\-_]{40,}',
    "Twilio Account SID": r'AC[0-9a-fA-F]{32}',
    "Twilio Auth Token": r'(?i)twilio_auth_token\s*[:=]\s*["\']?([0-9a-fA-F]{32})["\']?',
    "Discord Webhook": r'https://discord(?:app)?\.com/api/webhooks/[0-9]+/[0-9a-zA-Z_-]+',
    "Discord Bot Token": r'[MN][A-Za-z0-9_]{23}\.[A-Za-z0-9_]{6}\.[A-Za-z0-9_]{27}',
    "Telegram Bot Token": r'[0-9]{9,10}:[a-zA-Z0-9_-]{35}',
    "Heroku API Key": r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
    "Mailgun API Key": r'key-[0-9a-zA-Z]{32}',
    "SendGrid API Key": r'SG\.[0-9a-zA-Z_-]{22}\.[0-9a-zA-Z_-]{43}',
    "Facebook Access Token": r'EAACEdEose0c[0-9A-Za-z]+',
    "Database URL": r'(?:mongodb(?:\+srv)?|postgres|postgresql|mysql|mssql|redis):\/\/[^:\s]+:[^@\s]+@[^@\s]+',
    "Private Key": r'-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)? PRIVATE KEY-----',
    "JWT": r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
    "NPM Token": r'npm_[0-9a-zA-Z]{36}'
}

GENERIC_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b['\"]?([a-z0-9_\-\.]*(?:key|secret|token|password|passwd|pw|auth|cred|pass|db|uri|url)[a-z0-9_\-\.]*)['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.\/\+=]{16,})['\"]"
)

def calculate_entropy(s: str) -> float:
    if not s:
        return 0.0
    entropy = 0.0
    for x in range(256):
        p_x = float(s.count(chr(x))) / len(s)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy

def scan_for_secrets(text: str) -> list:
    if not text:
        return []
    findings = []
    matched_secrets = set()
    
    for line in text.splitlines():
        matched_any = False
        for name, pattern in SECRET_PATTERNS.items():
            m = re.search(pattern, line)
            if m:
                val = m.group(1) if m.groups() else m.group(0)
                if val and val not in matched_secrets:
                    matched_secrets.add(val)
                    findings.append({
                        "pattern_matched": name, 
                        "secret_redacted": str(val)[:6] + "..." + str(val)[-4:]
                    })
                    matched_any = True
                    
        if not matched_any:
            gen_match = GENERIC_ASSIGNMENT_PATTERN.search(line)
            if gen_match:
                val = gen_match.group(2)
                if val and val not in matched_secrets and calculate_entropy(val) >= 3.2:
                    matched_secrets.add(val)
                    findings.append({
                        "pattern_matched": f"High-Entropy Secret ({gen_match.group(1)})",
                        "secret_redacted": str(val)[:6] + "..." + str(val)[-4:]
                    })
    return findings

def scan_git_history(owner: str, repo_name: str):
    findings = []
    with tempfile.TemporaryDirectory() as td:
        repo_url = f"https://github.com/{owner}/{repo_name}.git"
        
        # 1. Shallow clone current state
        subprocess.run(["git", "clone", "--depth", "50", repo_url, td], capture_output=True, check=False)
        
        # 2. Scan active files (current tree) using Python walker for parity
        for root, _, files in os.walk(td):
            split_dirs = root.split(os.sep)
            if any(x in split_dirs for x in [".git", "node_modules", "venv", ".venv", "build_env", "dist", "build", "__pycache__"]):
                continue
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in [
                    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", 
                    ".pdf", ".zip", ".gz", ".tar", ".pyc", ".exe", 
                    ".dll", ".so", ".dylib", ".woff", ".woff2", ".ttf", ".eot",
                    ".tldr", ".drawio", ".map", ".mp3", ".mp4", ".mov", ".wav"
                ]: 
                    continue
                    
                if file.lower() in ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock", "composer.lock"]:
                    continue
                    
                # Skip the backend's own scanner script if it clones itself or exists
                if file in ["scanner.py", "leak_forensics.py", "sast_analyzer.py"]:
                    continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    for line_idx, line in enumerate(lines, 1):
                        matched_any = False
                        for name, pat in SECRET_PATTERNS.items():
                            m = re.search(pat, line)
                            if m:
                                val = m.group(1) if m.groups() else m.group(0)
                                findings.append({
                                    "pattern_matched": name,
                                    "commit_sha": f"Live:{os.path.relpath(filepath, td)}",
                                    "line": line_idx,
                                    "secret_redacted": str(val)[:6] + "..." + str(val)[-4:]
                                })
                                matched_any = True
                        
                        if not matched_any:
                            gen_match = GENERIC_ASSIGNMENT_PATTERN.search(line)
                            if gen_match:
                                val = gen_match.group(2)
                                if calculate_entropy(val) >= 3.2:
                                    findings.append({
                                        "pattern_matched": f"High-Entropy Secret ({gen_match.group(1)})",
                                        "commit_sha": f"Live:{os.path.relpath(filepath, td)}",
                                        "line": line_idx,
                                        "secret_redacted": str(val)[:6] + "..." + str(val)[-4:]
                                    })
                except Exception:
                    pass

        # 3. Check for Sensitive Files (Exposure Scan)
        SENSITIVE_FILES = [".env", "docker-compose.yml", "kubeconfig", "id_rsa", "config.json", "settings.py"]
        ls_res = subprocess.run(["git", "-C", td, "ls-files"], capture_output=True, text=True, check=False)
        if ls_res.stdout:
            for file_path in ls_res.stdout.splitlines():
                base_name = os.path.basename(file_path)
                if base_name in SENSITIVE_FILES or file_path.endswith((".pem", ".key")):
                    findings.append({
                        "pattern_matched": "Exposed Sensitive File",
                        "commit_sha": f"Live:{file_path}",
                        "secret_redacted": f"File Found: {base_name}"
                    })

        # 4. Scan commit history diffs (last 50 commits)
        log_res = subprocess.run(
            ["git", "-C", td, "log", "-p", "-n", "50"], 
            capture_output=True, text=True, check=False, timeout=60
        )
        if log_res.stdout:
            # We only look at added lines (starting with +)
            added_lines = "\n".join([line[1:] for line in log_res.stdout.splitlines() if line.startswith('+') and not line.startswith('+++')])
            diff_findings = scan_for_secrets(added_lines)
            for df in diff_findings:
                df["commit_sha"] = "Historical (Commit History)"
                df["line"] = None
                findings.append(df)

    # Deduplicate findings by redacted secret + pattern + location/sha
    unique_findings = []
    seen = set()
    for f in findings:
        key = f"{f['pattern_matched']}:{f['secret_redacted']}:{f.get('commit_sha')}:{f.get('line')}"
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    return unique_findings
