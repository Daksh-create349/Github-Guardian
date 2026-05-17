import httpx
import time
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

BACKEND_URL = "http://localhost:8000/api/v1"

def run_remote_scan(owner: str, repo: str, console):
    try:
        # 1. Trigger the asynchronous scan task on FastAPI
        with console.status("[bold cyan]Triggering remote forensic scan on Guardian Core...[/bold cyan]") as status:
            res = httpx.post(f"{BACKEND_URL}/scan", json={"owner": owner, "repo_name": repo}, timeout=10.0)
            if res.status_code != 200:
                console.print(f"[bold red]Failed to trigger scan. Status Code: {res.status_code}[/bold red]")
                console.print(res.text)
                return
            
            task_id = res.json().get("task_id")
            console.print(f"[green]Scan initiated successfully. Task ID:[/green] {task_id}\n")
            
        # 2. Poll the FastAPI backend for status updates
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Initializing scanners...", total=None)
            
            while True:
                status_res = httpx.get(f"{BACKEND_URL}/scan/status/{task_id}", timeout=10.0)
                if status_res.status_code != 200:
                    time.sleep(2)
                    continue
                    
                data = status_res.json()
                
                if data.get("status") == "completed":
                    progress.update(task, description="[bold green]Scan Completed! Processing AI Report...[/bold green]")
                    break
                elif data.get("status") == "failed":
                    progress.update(task, description=f"[bold red]Scan Failed: {data.get('error')}[/bold red]")
                    return
                else:
                    msg = data.get("message", "Processing pipelines...")
                    progress.update(task, description=f"[cyan]Engine Status:[/cyan] {msg}")
                    
                time.sleep(2)
                
        # 3. Download and Render the final AI enriched report
        res_data = httpx.get(f"{BACKEND_URL}/scan/status/{task_id}").json()
        report = res_data.get("report", {})
        
        score = report.get("score", 0.0)
        verdict = report.get("verdict", "Unknown")
        
        console.print("\n[bold underline]🛡️ GitHub Guardian Audit Report[/bold underline]")
        console.print(f"\nFinal AI Dampened Score: [bold {'red' if score > 5 else 'green'}]{score} / 10.0[/bold]")
        console.print(f"Verdict: [italic]{verdict}[/italic]\n")
        
        # Table of Actionable Findings
        if report.get("negatives"):
            vuln_table = Table(title="Actionable Architectural Threats", show_header=True, header_style="bold red")
            vuln_table.add_column("Issue Detected", style="white")
            
            for neg in report.get("negatives"):
                vuln_table.add_row(neg)
                
            console.print(vuln_table)
            
        if report.get("positives"):
            console.print("\n[bold green]Security Positives:[/bold green]")
            for pos in report.get("positives"):
                console.print(f"  [green]✔[/green] {pos}")
        
    except Exception as e:
        console.print(f"[bold red]Critical Error during remote scan orchestration:[/bold red] {str(e)}")
