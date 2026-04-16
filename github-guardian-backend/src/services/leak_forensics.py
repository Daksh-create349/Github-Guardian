import re
import tempfile
import subprocess
import os

# Professional-grade patterns
SECRET_PATTERNS = {
    "AWS Access Key": r'AKIA[0-9A-Z]{16}',
    "GitHub Token": r'ghp_[0-9a-zA-Z]{36}',
    "Slack Webhook": r'https://hooks\.slack\.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}/[0-9a-zA-Z]{24}',
    "Stripe API Key": r'sk_live_[0-9a-zA-Z]{24}',
    "Private Key": r'-----BEGIN (?:RSA|OPENSSH) PRIVATE KEY-----',
    "Google API Key": r'AIza[0-9A-Za-z\\-_]{35}'
}

def scan_for_secrets(text: str) -> list:
    if not text:
        return []
    findings = []
    matched_secrets = set()
    
    for name, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in matched_secrets:
                matched_secrets.add(match)
                findings.append({
                    "pattern_matched": name, 
                    "secret_redacted": str(match)[:6] + "..." + str(match)[-4:]
                })
    return findings

def scan_git_history(owner: str, repo_name: str):
    findings = []
    with tempfile.TemporaryDirectory() as td:
        repo_url = f"https://github.com/{owner}/{repo_name}.git"
        
        # 1. Shallow clone current state
        subprocess.run(["git", "clone", "--depth", "50", repo_url, td], capture_output=True, check=False)
        
        # 2. Scan active files (current tree)
        # We use git grep as it's lightning fast
        for name, pattern in SECRET_PATTERNS.items():
            res = subprocess.run(["git", "-C", td, "grep", "-E", pattern], capture_output=True, text=True, check=False)
            if res.stdout:
                for line in res.stdout.splitlines():
                    # Format: filename:matching_text
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        findings.append({
                            "pattern_matched": name,
                            "commit_sha": f"Live:{parts[0]}",
                            "secret_redacted": "REDACTED (Active File)"
                        })

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
        # BUG FIX: Added missing log command to prevent NameError
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
                findings.append(df)

    # Deduplicate findings by redacted secret + pattern
    unique_findings = []
    seen = set()
    for f in findings:
        key = f"{f['pattern_matched']}:{f['secret_redacted']}"
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    return unique_findings
