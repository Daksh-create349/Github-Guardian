import os
import re
import math
from rich.table import Table

# Robust set of enterprise-grade patterns
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

SAST_PATTERNS = {
    "SQL Injection (Raw Query)": r"\.execute\(\s*['\"].*['\"]\s*%\s*",
    "Insecure Rendering (XSS)": r"dangerouslySetInnerHTML",
    "Hardcoded Auth/Secret": r"password\s*=\s*['\"][^'\"]+['\"]"
}

def ask_gitignore(files):
    import sys
    try:
        with open("/dev/tty", "w") as tty_out, open("/dev/tty", "r") as tty_in:
            tty_out.write("\n⚠️  Would you like to automatically add these vulnerable files to .gitignore? (y/N): ")
            tty_out.flush()
            ans = tty_in.readline().strip().lower()
            return ans in ['y', 'yes']
    except Exception:
        ans = input("\n⚠️  Would you like to automatically add these vulnerable files to .gitignore? (y/N): ")
        return ans.lower() in ['y', 'yes']

def run_local_scan(path: str, console, hook_mode: bool = False) -> bool:
    console.print(f"[*] Scanning local directory: [yellow]{os.path.abspath(path)}[/yellow]...\n")
    findings = []
    
    for root, _, files in os.walk(path):
        # Ignore common build/dependency directories
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
                
            # Skip the scanner scripts themselves to prevent false positives!
            if file in ["scanner.py", "leak_forensics.py", "sast_analyzer.py"]:
                continue
                
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                for line_idx, line in enumerate(lines, 1):
                    # Check for Secrets
                    matched_any = False
                    for name, pat in SECRET_PATTERNS.items():
                        if re.search(pat, line):
                            findings.append((filepath, line_idx, "SECRET LEAK", name))
                            matched_any = True
                            
                    # If no specific patterns matched, check for generic high-entropy assignments
                    if not matched_any:
                        gen_match = GENERIC_ASSIGNMENT_PATTERN.search(line)
                        if gen_match:
                            val = gen_match.group(2)
                            # Only alert if value has high entropy
                            if calculate_entropy(val) >= 3.2:
                                findings.append((filepath, line_idx, "SECRET LEAK", f"High-Entropy Secret ({gen_match.group(1)})"))
                            
                    # Check for Semantic vulnerabilities
                    for name, pat in SAST_PATTERNS.items():
                        if re.search(pat, line):
                            findings.append((filepath, line_idx, "SAST VULN", name))
            except Exception:
                pass

    if not findings:
        console.print("[bold green]✅ No local leaks or vulnerabilities detected. Ready to push![/bold green]")
        return True
        
    table = Table(title="Guardian Local Shield Findings")
    table.add_column("File Path", style="cyan")
    table.add_column("Line", justify="right", style="magenta")
    table.add_column("Threat Class", style="yellow")
    table.add_column("Pattern Matched", style="red")
    
    for f in findings:
        table.add_row(os.path.relpath(f[0], path), str(f[1]), f[2], f[3])
        
    console.print(table)
    
    if hook_mode:
        vulnerable_files = list(set([os.path.relpath(f[0], path) for f in findings]))
        if ask_gitignore(vulnerable_files):
            gitignore_path = os.path.join(path, ".gitignore")
            with open(gitignore_path, "a") as gf:
                gf.write("\n# GitHub Guardian: Auto-ignored vulnerable files\n")
                for vf in vulnerable_files:
                    gf.write(f"{vf}\n")
            console.print("\n[bold green]✅ Vulnerable files appended to .gitignore![/bold green]")
            console.print("[yellow]Note: If the files were already tracked by git, you must also run 'git rm --cached <file>'.[/yellow]")
            console.print("[yellow]Please review your changes and try committing again.[/yellow]")
            return False

    console.print("\n[bold red]❌ SCAN FAILED! Active vulnerabilities were detected locally.[/bold red]")
    return False
