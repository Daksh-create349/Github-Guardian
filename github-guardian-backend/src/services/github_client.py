from github import Github
from src.core.config import settings

class GitHubClient:
    def __init__(self):
        self.g = Github(settings.github_token) if settings.github_token else Github()

    def get_repo_overview(self, owner: str, repo_name: str):
        try:
            repo = self.g.get_repo(f"{owner}/{repo_name}")
        except Exception as e:
            raise Exception(f"Repository '{owner}/{repo_name}' was not found on GitHub. Please check the name and your GITHUB_TOKEN permissions.")
            
        commits = list(repo.get_commits()[:5])
        try:
            workflows = repo.get_contents(".github/workflows")
            workflow_files = [wf.path for wf in workflows if wf.type == "file"]
        except:
            workflow_files = []
            
        return {
            "name": repo.name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "recent_commits": [{"sha": c.sha, "message": c.commit.message} for c in commits],
            "workflow_files": workflow_files
        }

    def get_repo_contents(self, owner: str, repo_name: str, path: str):
        repo = self.g.get_repo(f"{owner}/{repo_name}")
        content = repo.get_contents(path)
        return content.decoded_content.decode('utf-8')

    def get_issues_and_prs(self, owner: str, repo_name: str):
        repo = self.g.get_repo(f"{owner}/{repo_name}")
        issues = list(repo.get_issues(state='open')[:10])
        return [{"title": i.title, "body": i.body} for i in issues]

github_client = GitHubClient()
