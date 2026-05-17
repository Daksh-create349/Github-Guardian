import os
import re
from rich.table import Table

# Re-using the professional-grade patterns from the backend
SECRET_PATTERNS = {
    "AWS Access Key": r'AKIA[0-9A-Z]{16}',
    "GitHub Token": r'ghp_[0-9a-zA-Z]{36}',
    "Slack Webhook": r'https://hooks\.slack\.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}/[0-9a-zA-Z]{24}',
    "Stripe API Key": r'sk_live_[0-9a-zA-Z]{24}',
    "Private Key": r'-----BEGIN (?:RSA|OPENSSH) PRIVATE KEY-----',
    "Google API Key": r'AIza[0-9A-Za-z\-_]{35}',
    "OpenAI API Key": r'sk\s*-\s*[a-zA-Z0-9\-_]{40,}'
}

SAST_PATTERNS = {
    "SQL Injection (Raw Query)": r"\.execute\(\".*%\s*\"",
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
        if any(x in root for x in [".git", "node_modules", "venv", "__pycache__"]):
            continue
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in [".png", ".jpg", ".pdf", ".zip", ".pyc"]: 
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
                    for name, pat in SECRET_PATTERNS.items():
                        if re.search(pat, line):
                            findings.append((filepath, line_idx, "SECRET LEAK", name))
                            
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
