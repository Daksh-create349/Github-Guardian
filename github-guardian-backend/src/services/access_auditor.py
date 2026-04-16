from .github_client import github_client
from datetime import datetime, timezone

def audit_repo_access(owner: str, repo_name: str):
    findings = {
        "stale_deploy_keys": [],
        "missing_branch_protection": []
    }
    
    try:
        repo = github_client.g.get_repo(f"{owner}/{repo_name}")
        
        # Check Deploy Keys
        try:
            keys = repo.get_keys()
            now = datetime.now(timezone.utc)
            for k in keys:
                # If PyGithub provides created_at (otherwise we skip)
                if hasattr(k, 'created_at') and k.created_at:
                    age_days = (now - k.created_at.replace(tzinfo=timezone.utc)).days
                    if age_days > 90:
                        findings["stale_deploy_keys"].append({
                            "title": k.title,
                            "age_days": age_days,
                            "issue": "Stale deploy key (> 90 days)"
                        })
        except Exception:
            pass
            
        # Check Branch Protection for Default Branch
        default_branch = repo.default_branch or "main"
        try:
            branch = repo.get_branch(default_branch)
            if not branch.protected:
                findings["missing_branch_protection"].append(default_branch)
        except Exception:
            findings["missing_branch_protection"].append(default_branch)
            
    except Exception as e:
        # Permission denied or 404
        pass
        
    return findings
