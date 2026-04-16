import json
import asyncio
from src.core.database import scan_storage
from src.services.github_client import github_client
from src.services.leak_forensics import scan_git_history
from src.services.oops_analyzer import analyze_oops_commits
from src.services.ci_cd_analyzer import analyze_workflows
from src.services.supply_chain import generate_sbom_and_scan
from src.services.access_auditor import audit_repo_access
from src.services.dependency_confusion import check_dependency_confusion
from src.services.sast_analyzer import analyze_code_semantics
from src.services.ai_reviewer import generate_ai_code_review
from src.services.ai_interpreter import interpret_finding, generate_repo_report

async def run_security_scan(task_id: str, owner: str, repo_name: str):
    try:
        # Step 1: Metadata
        scan_storage.set(task_id, {"status": "processing", "message": "Fetching repository overview..."})
        repo_info = await asyncio.to_thread(github_client.get_repo_overview, owner, repo_name)
        
        # Step 2: Forensic Scan
        scan_storage.set(task_id, {"status": "processing", "message": "Cloning and scanning full git history..."})
        secret_findings = await asyncio.to_thread(scan_git_history, owner, repo_name)
        
        # Step 3: Semantic Audit (SAST)
        scan_storage.set(task_id, {"status": "processing", "message": "Performing Semantic Code Audit (SQLi, XSS)..."})
        sast_findings = await asyncio.to_thread(analyze_code_semantics, owner, repo_name)

        # Step 4: AI Technical Review
        scan_storage.set(task_id, {"status": "processing", "message": "Generating AI-driven Code Review..."})
        code_review = await asyncio.to_thread(generate_ai_code_review, owner, repo_name)

        # Step 5: Legacy checks
        scan_storage.set(task_id, {"status": "processing", "message": "Analyzing commit history for 'oops' patterns..."})
        oops_commits = await asyncio.to_thread(analyze_oops_commits, owner, repo_name)

        scan_storage.set(task_id, {"status": "processing", "message": "Auditing CI/CD & Dependencies..."})
        # (Workflow and dependency logic remains same)
        workflow_contents = []
        for wf_path in repo_info.get("workflow_files", []):
            try:
                content = await asyncio.to_thread(github_client.get_repo_contents, owner, repo_name, wf_path)
                workflow_contents.append(content)
            except: pass
        ci_cd_issues = analyze_workflows(workflow_contents)

        dependency_issues = []
        try:
            pkg_json = await asyncio.to_thread(github_client.get_repo_contents, owner, repo_name, "package.json")
            dependency_issues = await check_dependency_confusion(pkg_json)
        except: pass

        scan_storage.set(task_id, {"status": "processing", "message": "Generating Supply Chain SBOM (Grype/Syft)..."})
        supply_chain = await asyncio.to_thread(generate_sbom_and_scan, owner, repo_name)
        
        scan_storage.set(task_id, {"status": "processing", "message": "Finalizing Security Permissions Audit..."})
        access_permissions = await asyncio.to_thread(audit_repo_access, owner, repo_name)

        findings = {
            "secret_findings": secret_findings,
            "sast_findings": sast_findings,
            "code_review": code_review,
            "ci_cd_issues": ci_cd_issues, 
            "oops_commits": oops_commits,
            "supply_chain": supply_chain,
            "access_permissions": access_permissions,
            "dependency_issues": dependency_issues
        }

        # AI Enrichment
        enrichment_tasks = []
        async def enrich(f):
            f["ai_insight"] = await asyncio.to_thread(interpret_finding, str(f))

        for group in [secret_findings, sast_findings, ci_cd_issues]:
            for item in group:
                enrichment_tasks.append(enrich(item))
        
        if enrichment_tasks:
            await asyncio.gather(*enrichment_tasks)

        # Final Branding & Scoring
        scan_storage.set(task_id, {"status": "processing", "message": "Generating FINAL Guardian Audit Report..."})
        report = await asyncio.to_thread(generate_repo_report, findings, repo_info)

        scan_storage.set(task_id, {
            "status": "completed", 
            "result": findings,
            "report": report
        })
        
    except Exception as e:
        scan_storage.set(task_id, {"status": "failed", "error": str(e)})
