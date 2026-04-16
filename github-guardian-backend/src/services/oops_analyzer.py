from .github_client import github_client
from .leak_forensics import scan_for_secrets
import httpx

OOPS_KEYWORDS = ['fix typo', 'tmp', 'wip', 'test pls ignore', 'remove key', 'oops', 'cleanup']

def analyze_oops_commits(owner: str, repo_name: str):
    alerts = []
    try:
        repo = github_client.g.get_repo(f"{owner}/{repo_name}")
        commits = repo.get_commits()[:30]
        
        for c in commits:
            msg = c.commit.message.lower()
            if any(k in msg for k in OOPS_KEYWORDS):
                # Fetch patch
                patch_url = c.html_url + ".patch"
                res = httpx.get(patch_url)
                if res.status_code == 200:
                    diff = res.text
                    # Check for secrets only in removed lines (- )
                    removed_lines = [line[1:] for line in diff.splitlines() if line.startswith('-') and not line.startswith('---')]
                    for line in removed_lines:
                        secrets = scan_for_secrets(line)
                        if secrets:
                            alerts.append({
                                "commit_message": c.commit.message,
                                "sha": c.sha,
                                "secret_redacted": secrets[0]['secret_redacted'],
                                "original_pattern": secrets[0]['pattern_matched']
                            })
                            break # Only raise one alert per commit to reduce noise
        return alerts
    except Exception as e:
        return []
