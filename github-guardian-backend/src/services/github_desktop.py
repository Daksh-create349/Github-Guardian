import os
import re
import base64
from github import Github, GithubException
from src.core.config import settings

# ─── Sensitivity Rules ───────────────────────────────────────────────────────

SENSITIVE_FILE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development", ".env.staging",
    ".env.test", "id_rsa", "id_rsa.pub", "id_ed25519", "id_ed25519.pub",
    "secrets.json", "credentials.json", "service-account.json",
    "kubeconfig", "docker-compose.override.yml",
}

SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".crt", ".cer", ".ppk"}

SENSITIVE_FOLDERS = {
    "node_modules", "venv", ".venv", "env", "ENV",
    "__pycache__", "dist", "build", ".next", ".nuxt",
    ".git", ".idea", "coverage", ".pytest_cache",
}

# Map from detected category → gitignore block
GITIGNORE_BLOCKS = {
    "env":     ("# Environment Variables & Secrets",
                [".env", ".env.*", ".env.local", ".env.production", ".env.development",
                 ".env.staging", ".env.test", "*.secret", "secrets.json", "credentials.json"]),
    "keys":    ("# Private Keys & Certificates",
                ["*.pem", "*.key", "*.p12", "*.pfx", "*.crt", "*.cer", "*.ppk",
                 "id_rsa", "id_rsa.pub", "id_ed25519", "id_ed25519.pub"]),
    "node":    ("# Node.js Dependencies",
                ["node_modules/", "npm-debug.log*", "yarn-debug.log*",
                 "yarn-error.log*", ".npm", ".yarn-integrity"]),
    "python":  ("# Python Environment & Cache",
                ["venv/", ".venv/", "env/", "ENV/", "__pycache__/",
                 "*.py[cod]", "*.pyo", ".pytest_cache/", "*.egg-info/",
                 "dist/", "build/", ".eggs/"]),
    "build":   ("# Build Artifacts",
                ["dist/", "build/", "out/", ".next/", ".nuxt/", ".output/"]),
    "ide":     ("# IDE & Editor Files",
                [".idea/", ".vscode/", "*.swp", "*.swo", "*~", ".DS_Store", "Thumbs.db"]),
    "logs":    ("# Logs & Runtime",
                ["*.log", "logs/", "*.pid", "*.seed", "*.pid.lock"]),
}

ALWAYS_BLOCKS = ["ide", "logs"]  # Always added regardless of what's found


# ─── Gitignore Generator ──────────────────────────────────────────────────────

def detect_sensitive_and_build_gitignore(file_names: list) -> tuple:
    """
    Scan uploaded file names and build a targeted .gitignore.
    Returns (detected_items: list[dict], gitignore_content: str)
    """
    detected_items = []
    needed_blocks = set(ALWAYS_BLOCKS)

    for raw_name in file_names:
        name = raw_name.replace("\\", "/")
        base = name.split("/")[-1]
        ext = os.path.splitext(base)[1].lower()
        parts = name.split("/")

        # Check exact file name
        if base in SENSITIVE_FILE_NAMES or base.startswith(".env"):
            needed_blocks.add("env")
            detected_items.append({
                "file": base,
                "reason": "Contains environment variables or secrets",
                "action": "Will be listed in .gitignore"
            })

        # Check extension
        if ext in SENSITIVE_EXTENSIONS:
            needed_blocks.add("keys")
            detected_items.append({
                "file": base,
                "reason": f"Private key or certificate file ({ext})",
                "action": "Will be listed in .gitignore"
            })

        # Check folder names in path
        for part in parts[:-1]:  # exclude filename itself
            if part in SENSITIVE_FOLDERS:
                if part == "node_modules":
                    needed_blocks.add("node")
                    detected_items.append({
                        "file": f"{part}/",
                        "reason": "Node.js dependency folder (can be 100MB+)",
                        "action": "Excluded — easily re-installed via npm install"
                    })
                elif part in {"venv", ".venv", "env", "ENV", "__pycache__"}:
                    needed_blocks.add("python")
                    detected_items.append({
                        "file": f"{part}/",
                        "reason": "Python environment or cache folder",
                        "action": "Excluded — re-create with pip install -r requirements.txt"
                    })
                elif part in {"dist", "build", ".next", ".nuxt", "out"}:
                    needed_blocks.add("build")
                    detected_items.append({
                        "file": f"{part}/",
                        "reason": "Build output folder (generated files)",
                        "action": "Excluded — re-generate with your build command"
                    })
                elif part in {".idea", ".vscode"}:
                    pass  # already in 'ide' always block

    # De-duplicate detected items
    seen = set()
    unique_detected = []
    for item in detected_items:
        if item["file"] not in seen:
            seen.add(item["file"])
            unique_detected.append(item)

    # Build .gitignore content
    lines = [
        "# ============================================================",
        "# .gitignore — Auto-generated by GitHub Guardian Desktop",
        "# This file protects your repo from accidental secret exposure.",
        "# ============================================================",
        "",
    ]

    for block_key in ALWAYS_BLOCKS + [b for b in needed_blocks if b not in ALWAYS_BLOCKS]:
        if block_key in GITIGNORE_BLOCKS:
            header, rules = GITIGNORE_BLOCKS[block_key]
            lines.append(header)
            lines.extend(rules)
            lines.append("")

    return unique_detected, "\n".join(lines)


# ─── Name Availability ────────────────────────────────────────────────────────

def check_repo_name_availability(repo_name: str, github_token: str = None) -> dict:
    """Check if a GitHub repo name is available for the authenticated user."""
    token = github_token or settings.github_token
    g = Github(token)
    user = g.get_user()
    username = user.login

    # Sanitize: GitHub only allows alphanumeric, hyphens, underscores, dots
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "-", repo_name).strip("-").strip(".")
    if not safe_name:
        safe_name = "my-project"
    # Truncate to 100 chars (GitHub limit)
    safe_name = safe_name[:100]

    def name_exists(name):
        try:
            user.get_repo(name)
            return True
        except GithubException:
            return False

    is_available = not name_exists(safe_name)

    suggestions = []
    if not is_available:
        for suffix in ["-app", "-project", "-v2", "-main", "-repo", "-2025", "-2026"]:
            candidate = (safe_name + suffix)[:100]
            if not name_exists(candidate):
                suggestions.append(candidate)
            if len(suggestions) >= 3:
                break

    return {
        "available": is_available,
        "username": username,
        "sanitized_name": safe_name,
        "suggestions": suggestions,
    }


# ─── Create Repo & Push Files ─────────────────────────────────────────────────

SKIP_FOLDER_PREFIXES = {
    "node_modules", "venv", ".venv", "__pycache__", "dist",
    "build", ".git", ".next", ".nuxt", "coverage", ".pytest_cache",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per file limit


def should_skip_file(rel_path: str) -> tuple:
    """Returns (skip: bool, reason: str)"""
    parts = rel_path.replace("\\", "/").split("/")
    base = parts[-1]
    ext = os.path.splitext(base)[1].lower()

    # Skip folders
    for part in parts[:-1]:
        if part in SKIP_FOLDER_PREFIXES:
            return True, f"Inside excluded folder ({part}/)"

    # Skip the file itself if it's a top-level sensitive folder marker
    if base in SKIP_FOLDER_PREFIXES:
        return True, "Excluded folder"

    # Skip .git internals
    if ".git" in parts:
        return True, "Git internals"

    return False, ""


def create_repo_and_push(
    repo_name: str,
    description: str,
    private: bool,
    commit_message: str,
    files: list,  # list of (filename: str, content: bytes) tuples
    github_token: str = None,  # User's OAuth token (preferred over .env server token)
) -> dict:
    """
    Creates a GitHub repository and pushes all files in a single commit.
    Automatically generates and includes a .gitignore.
    """
    from github import InputGitTreeElement  # import here to avoid top-level issues

    token = github_token or settings.github_token
    g = Github(token)
    user = g.get_user()

    # ── Detect sensitive files & generate .gitignore ──
    all_names = [f[0] for f in files]
    detected_sensitive, gitignore_content = detect_sensitive_and_build_gitignore(all_names)

    # ── Filter files (skip sensitive folders, oversized files) ──
    safe_files = []
    skipped_files = []
    for fname, content_bytes in files:
        skip, reason = should_skip_file(fname)
        if skip:
            skipped_files.append({"file": fname, "reason": reason})
            continue
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            skipped_files.append({"file": fname, "reason": "File too large (>50MB)"})
            continue
        safe_files.append((fname, content_bytes))

    # ── Create the repository ──
    repo = user.create_repo(
        name=repo_name,
        description=description or "Created with GitHub Guardian Desktop",
        private=private,
        auto_init=False,
    )

    try:
        # Step 1: Initialize repo with .gitignore (creates the first commit + default branch)
        repo.create_file(
            path=".gitignore",
            message="Initial commit: Add auto-generated .gitignore",
            content=gitignore_content.encode("utf-8"),
        )

        if not safe_files:
            return {
                "success": True,
                "repo_url": repo.html_url,
                "clone_url": repo.clone_url,
                "files_pushed": 0,
                "files_skipped": len(skipped_files),
                "skipped_files": skipped_files,
                "detected_sensitive": detected_sensitive,
                "gitignore_content": gitignore_content,
            }

        # Step 2: Get the branch ref / latest commit / base tree
        main_branch = repo.default_branch
        ref = repo.get_git_ref(f"heads/{main_branch}")
        latest_sha = ref.object.sha
        latest_commit = repo.get_git_commit(latest_sha)
        base_tree = repo.get_git_tree(latest_commit.tree.sha)

        # Step 3: Create blobs for every user file and build InputGitTreeElement list
        tree_elements = []
        pushed_files = []
        blob_errors = []

        for fname, content_bytes in safe_files:
            clean_path = fname.replace("\\", "/").lstrip("/")
            try:
                # Try as UTF-8 text first
                try:
                    text_content = content_bytes.decode("utf-8")
                    blob = repo.create_git_blob(text_content, "utf-8")
                except UnicodeDecodeError:
                    # Binary file (images, zips, etc.) → base64 encoding
                    b64 = base64.b64encode(content_bytes).decode("ascii")
                    blob = repo.create_git_blob(b64, "base64")

                # Use InputGitTreeElement (required by current PyGithub versions)
                tree_elements.append(
                    InputGitTreeElement(
                        path=clean_path,
                        mode="100644",
                        type="blob",
                        sha=blob.sha,
                    )
                )
                pushed_files.append(clean_path)

            except GithubException as ge:
                blob_errors.append({"file": clean_path, "reason": f"GitHub API error: {ge.data}"})
            except Exception as ex:
                blob_errors.append({"file": clean_path, "reason": str(ex)})

        if not tree_elements:
            raise Exception(
                f"No files could be uploaded. Errors: {blob_errors}"
            )

        # Step 4: Create a new git tree (snapshot of all files)
        new_tree = repo.create_git_tree(tree_elements, base_tree=base_tree)

        # Step 5: Create the commit pointing to the new tree
        new_commit = repo.create_git_commit(
            message=commit_message or "Initial commit via GitHub Guardian Desktop",
            tree=new_tree,
            parents=[latest_commit],
        )

        # Step 6: Advance the branch HEAD to the new commit
        ref.edit(new_commit.sha)

        return {
            "success": True,
            "repo_url": repo.html_url,
            "clone_url": repo.clone_url,
            "files_pushed": len(pushed_files),
            "pushed_files": pushed_files,
            "files_skipped": len(skipped_files) + len(blob_errors),
            "skipped_files": skipped_files + blob_errors,
            "detected_sensitive": detected_sensitive,
            "gitignore_content": gitignore_content,
        }

    except GithubException as ge:
        # Clean up: delete the partially-created repo
        try:
            repo.delete()
        except Exception:
            pass
        # Extract a clean error message from GitHub's response
        detail = ge.data if isinstance(ge.data, str) else str(ge.data.get("message", ge.data) if isinstance(ge.data, dict) else ge.data)
        raise Exception(f"GitHub API error ({ge.status}): {detail}")

    except Exception as e:
        try:
            repo.delete()
        except Exception:
            pass
        raise Exception(f"Push failed: {str(e)}")

