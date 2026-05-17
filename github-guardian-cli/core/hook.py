import os
import stat
import platform

HOOK_SCRIPT = """#!/usr/bin/env bash
# GitHub Guardian Pre-Commit Shield

echo "🛡️ GitHub Guardian: Running Pre-Commit Shield Audit..."

# Run the globally installed guardian command
guardian scan-local . --hook

if [ $? -ne 0 ]; then
    echo "❌ COMMIT BLOCKED! Secrets or semantic vulnerabilities were detected in your staging area."
    echo "Please fix the issues. To bypass the shield (NOT RECOMMENDED), use 'git commit --no-verify'."
    exit 1
fi

echo "✅ Code looks clean. Proceeding with commit."
exit 0
"""

import subprocess

def install_pre_commit_hook(console):
    try:
        git_root_proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        git_root = git_root_proc.stdout.strip()
    except Exception:
        console.print("[bold red]Error:[/bold red] Not inside a git repository. Cannot install hook.")
        return
        
    git_dir = os.path.join(git_root, ".git")
    hook_path = os.path.join(git_dir, "hooks", "pre-commit")
    
    try:
        with open(hook_path, "w") as f:
            f.write(HOOK_SCRIPT)
            
        # Make the bash script executable (Unix/macOS only)
        if platform.system() != 'Windows':
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
        
        console.print(f"[bold green]✅ Success![/bold green] Pre-commit shield installed at: {hook_path}")
        console.print("[italic]Your commits will now be securely blocked if secrets or SAST vulnerabilities are staged.[/italic]")
    except Exception as e:
        console.print(f"[bold red]Failed to install hook:[/bold red] {str(e)}")
