import typer
from rich.console import Console
from rich.panel import Panel
from core.scanner import run_local_scan
from core.remote import run_remote_scan
from core.hook import install_pre_commit_hook

app = typer.Typer(help="GitHub Guardian - Forensic Security Audit CLI")
console = Console()

@app.command()
def scan_local(
    path: str = typer.Argument(".", help="Path to scan locally"),
    hook_mode: bool = typer.Option(False, "--hook", help="Run in git hook mode (prompts to gitignore)")
):
    """Scan local directory for exposed secrets and vulnerabilities before committing."""
    console.print(Panel.fit("[bold cyan]GitHub Guardian[/bold cyan] - Local Shield", border_style="cyan"))
    run_local_scan(path, console, hook_mode)

@app.command()
def scan_remote(owner: str = typer.Argument(..., help="GitHub Repository Owner"), 
                repo: str = typer.Argument(..., help="GitHub Repository Name")):
    """Trigger an AI-driven forensic scan on the Guardian backend."""
    console.print(Panel.fit(f"[bold magenta]GitHub Guardian[/bold magenta] - Remote Scan: {owner}/{repo}", border_style="magenta"))
    run_remote_scan(owner, repo, console)

@app.command()
def hook_install():
    """Install the Pre-Commit Shield to block insecure commits."""
    console.print(Panel.fit("[bold green]GitHub Guardian[/bold green] - Pre-Commit Hook", border_style="green"))
    install_pre_commit_hook(console)

if __name__ == "__main__":
    app()
