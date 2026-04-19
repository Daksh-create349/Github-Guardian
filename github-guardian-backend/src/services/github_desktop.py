import os
import re
import base64
from datetime import datetime
from github import Github, GithubException, InputGitTreeElement
from src.core.config import settings
from src.services.conflict_resolver import resolve_file_conflict
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


async def smart_push_to_existing_repo(
    repo_name: str,
    commit_message: str,
    files: list,  # list of (filename: str, content: bytes) tuples
    github_token: str
) -> dict:
    """
    Pushes files to an existing GitHub repository.
    1. Creates a new branch off the default branch.
    2. Compares incoming files with remote files.
    3. Resolves conflicts using AI if necessary.
    4. Commits to new branch, creates PR, and auto-merges it.
    """
    g = Github(github_token)
    user = g.get_user()

    try:
        repo = user.get_repo(repo_name)
    except GithubException:
        raise Exception(f"Repository '{repo_name}' not found. Make sure it exists.")

    default_branch = repo.default_branch
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    new_branch_name = f"guardian-update-{timestamp}"

    # 1. Get default branch ref to base the new branch on
    ref = repo.get_git_ref(f"heads/{default_branch}")
    latest_sha = ref.object.sha
    latest_commit = repo.get_git_commit(latest_sha)
    base_tree = repo.get_git_tree(latest_commit.tree.sha, recursive=True)

    # 2. Create the new branch
    repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=latest_sha)

    # Map existing files in tree for quick lookup
    existing_files = {element.path: element for element in base_tree.tree if element.type == "blob"}

    skipped_files = []
    tree_elements = []
    pushed_files = []
    conflict_resolutions = []

    for fname, content_bytes in files:
        skip, reason = should_skip_file(fname)
        if skip:
            skipped_files.append({"file": fname, "reason": reason})
            continue

        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            skipped_files.append({"file": fname, "reason": "File too large (>50MB)"})
            continue

        clean_path = fname.replace("\\", "/").lstrip("/")
        
        # Determine if we need to auto-resolve conflict
        final_content_bytes = content_bytes
        if clean_path in existing_files: # File already exists on remote
            try:
                # Try to decode as text for AI resolution
                local_text = content_bytes.decode("utf-8")
                
                # Fetch remote content
                remote_blob = repo.get_git_blob(existing_files[clean_path].sha)
                if remote_blob.encoding == "base64":
                    remote_bytes = base64.b64decode(remote_blob.content)
                    try:
                        remote_text = remote_bytes.decode("utf-8")
                        
                        # Only invoke AI if contents actually differ
                        if local_text != remote_text:
                            resolved_text = await resolve_file_conflict(clean_path, remote_text, local_text)
                            final_content_bytes = resolved_text.encode("utf-8")
                            conflict_resolutions.append(clean_path)
                    except UnicodeDecodeError:
                        # Remote is binary, just overwrite with local
                        pass
            except UnicodeDecodeError:
                # Local is binary, cannot use AI, just overwrite
                pass

        # Create Blob
        try:
            try:
                text_content = final_content_bytes.decode("utf-8")
                blob = repo.create_git_blob(text_content, "utf-8")
            except UnicodeDecodeError:
                b64 = base64.b64encode(final_content_bytes).decode("ascii")
                blob = repo.create_git_blob(b64, "base64")

            tree_elements.append(
                InputGitTreeElement(
                    path=clean_path,
                    mode="100644",
                    type="blob",
                    sha=blob.sha,
                )
            )
            pushed_files.append(clean_path)
        except Exception as ex:
            skipped_files.append({"file": clean_path, "reason": str(ex)})

    if not tree_elements:
        # Delete branch if nothing to push
        repo.get_git_ref(f"heads/{new_branch_name}").delete()
        raise Exception("No files could be successfully processed.")

    # 3. Create Tree and Commit
    new_tree = repo.create_git_tree(tree_elements, base_tree=repo.get_git_tree(latest_commit.tree.sha))
    new_commit = repo.create_git_commit(
        message=commit_message or f"Guardian auto-update {timestamp}",
        tree=new_tree,
        parents=[latest_commit],
    )

    # 4. Update the new branch
    repo.get_git_ref(f"heads/{new_branch_name}").edit(new_commit.sha)

    # 5. Create Pull Request
    pr = repo.create_pull(
        title=f"Guardian Auto-Update: {commit_message or timestamp}",
        body="Automated PR created by GitHub Guardian Desktop. \n\nConflicts automatically resolved by AI.",
        head=new_branch_name,
        base=default_branch
    )

    # 6. Auto-merge the PR
    merge_status = pr.merge(merge_method="squash")

    # 7. Cleanup the branch after merge
    try:
        repo.get_git_ref(f"heads/{new_branch_name}").delete()
    except:
        pass # Ignore cleanup failure

    return {
        "success": True,
        "repo_url": repo.html_url,
        "clone_url": repo.clone_url,
        "files_pushed": len(pushed_files),
        "pushed_files": pushed_files,
        "files_skipped": len(skipped_files),
        "skipped_files": skipped_files,
        "conflict_resolutions": conflict_resolutions,
        "pr_url": pr.html_url,
        "merged": merge_status.merged
    }


def create_new_branch(repo_name: str, new_branch_name: str, base_branch: str, github_token: str) -> dict:
    """
    Creates a new branch off a base branch in the given repository.
    """
    g = Github(github_token)
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
    except GithubException:
        raise Exception(f"Repository '{repo_name}' not found.")

    # Sanitize branch name
    safe_name = re.sub(r"[^a-zA-Z0-9._\-/]", "-", new_branch_name).strip("-")
    if not safe_name:
        safe_name = f"feature-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # Check if branch already exists
    try:
        repo.get_git_ref(f"heads/{safe_name}")
        raise Exception(f"Branch '{safe_name}' already exists.")
    except GithubException:
        pass  # Good — it doesn't exist

    # Get base branch SHA
    try:
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
    except GithubException:
        raise Exception(f"Base branch '{base_branch}' not found.")

    # Create new branch
    repo.create_git_ref(ref=f"refs/heads/{safe_name}", sha=base_ref.object.sha)

    return {
        "success": True,
        "branch_name": safe_name,
        "base_branch": base_branch,
        "repo_url": repo.html_url,
    }


def push_files_to_branch(
    repo_name: str,
    branch_name: str,
    commit_message: str,
    files: list,  # list of (filename, content_bytes)
    github_token: str,
) -> dict:
    """
    Pushes files directly to a specific branch WITHOUT creating a PR.
    Used after the user creates a new branch and wants to add files to it.
    """
    g = Github(github_token)
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
    except GithubException:
        raise Exception(f"Repository '{repo_name}' not found.")

    try:
        ref = repo.get_git_ref(f"heads/{branch_name}")
    except GithubException:
        raise Exception(f"Branch '{branch_name}' not found.")

    latest_sha = ref.object.sha
    latest_commit = repo.get_git_commit(latest_sha)
    base_tree = repo.get_git_tree(latest_commit.tree.sha)

    skipped_files = []
    tree_elements = []
    pushed_files = []

    for fname, content_bytes in files:
        skip, reason = should_skip_file(fname)
        if skip:
            skipped_files.append({"file": fname, "reason": reason})
            continue
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            skipped_files.append({"file": fname, "reason": "File too large (>50MB)"})
            continue

        clean_path = fname.replace("\\", "/").lstrip("/")
        try:
            try:
                blob = repo.create_git_blob(content_bytes.decode("utf-8"), "utf-8")
            except UnicodeDecodeError:
                blob = repo.create_git_blob(base64.b64encode(content_bytes).decode("ascii"), "base64")

            tree_elements.append(InputGitTreeElement(path=clean_path, mode="100644", type="blob", sha=blob.sha))
            pushed_files.append(clean_path)
        except Exception as ex:
            skipped_files.append({"file": clean_path, "reason": str(ex)})

    if not tree_elements:
        raise Exception("No files could be pushed.")

    new_tree = repo.create_git_tree(tree_elements, base_tree=base_tree)
    new_commit = repo.create_git_commit(
        message=commit_message or f"Push to {branch_name} via GitHub Guardian",
        tree=new_tree,
        parents=[latest_commit],
    )
    ref.edit(new_commit.sha)

    return {
        "success": True,
        "branch_name": branch_name,
        "files_pushed": len(pushed_files),
        "pushed_files": pushed_files,
        "files_skipped": len(skipped_files),
        "skipped_files": skipped_files,
        "repo_url": repo.html_url,
    }


async def merge_with_conflict_check(
    repo_name: str,
    source_branch: str,
    target_branch: str,
    github_token: str,
) -> dict:
    """
    The smart merge flow:
    1. Compare files between source and target branch.
    2. If no conflicts → create PR and merge directly.
    3. If conflicts → try AI resolution on each conflicting file.
    4. If AI fixes all → push resolved files to source → merge PR.
    5. If AI cannot fix some → return unfixable list to user.
    """
    g = Github(github_token)
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
    except GithubException:
        raise Exception(f"Repository '{repo_name}' not found.")

    # Get tree of both branches
    source_ref = repo.get_git_ref(f"heads/{source_branch}")
    target_ref = repo.get_git_ref(f"heads/{target_branch}")

    source_commit = repo.get_git_commit(source_ref.object.sha)
    target_commit = repo.get_git_commit(target_ref.object.sha)

    source_tree = {e.path: e for e in repo.get_git_tree(source_commit.tree.sha, recursive=True).tree if e.type == "blob"}
    target_tree = {e.path: e for e in repo.get_git_tree(target_commit.tree.sha, recursive=True).tree if e.type == "blob"}

    # Find files that exist in BOTH branches but have DIFFERENT SHAs (potential conflicts)
    conflicting_files = [
        path for path in source_tree
        if path in target_tree and source_tree[path].sha != target_tree[path].sha
    ]

    conflict_results = {
        "total_conflicts": len(conflicting_files),
        "ai_fixed": [],
        "ai_failed": [],
    }

    if conflicting_files:
        # Try AI resolution for each conflicting file
        resolution_tree_elements = []

        for path in conflicting_files:
            try:
                source_blob = repo.get_git_blob(source_tree[path].sha)
                target_blob = repo.get_git_blob(target_tree[path].sha)

                src_bytes = base64.b64decode(source_blob.content) if source_blob.encoding == "base64" else source_blob.content.encode("utf-8")
                tgt_bytes = base64.b64decode(target_blob.content) if target_blob.encoding == "base64" else target_blob.content.encode("utf-8")

                try:
                    src_text = src_bytes.decode("utf-8")
                    tgt_text = tgt_bytes.decode("utf-8")

                    if src_text == tgt_text:
                        continue  # Same content, no real conflict

                    resolved = await resolve_file_conflict(path, tgt_text, src_text)
                    blob = repo.create_git_blob(resolved, "utf-8")
                    resolution_tree_elements.append(
                        InputGitTreeElement(path=path, mode="100644", type="blob", sha=blob.sha)
                    )
                    conflict_results["ai_fixed"].append(path)
                except UnicodeDecodeError:
                    # Binary file conflict — cannot auto-resolve
                    conflict_results["ai_failed"].append(path)

            except Exception as ex:
                conflict_results["ai_failed"].append(path)

        # If there are unfixable conflicts, stop and tell user
        if conflict_results["ai_failed"]:
            return {
                "success": False,
                "merged": False,
                "reason": "conflict_unfixable",
                "conflict_results": conflict_results,
                "message": f"We tried our best but could not automatically fix conflicts in: {', '.join(conflict_results['ai_failed'])}. Please resolve these manually.",
            }

        # Push AI-resolved files back to source branch
        if resolution_tree_elements:
            src_ref = repo.get_git_ref(f"heads/{source_branch}")
            src_commit = repo.get_git_commit(src_ref.object.sha)
            resolved_tree = repo.create_git_tree(resolution_tree_elements, base_tree=repo.get_git_tree(src_commit.tree.sha))
            resolved_commit = repo.create_git_commit(
                message=f"Guardian AI: Auto-resolve conflicts before merge into {target_branch}",
                tree=resolved_tree,
                parents=[src_commit],
            )
            src_ref.edit(resolved_commit.sha)

    # Create and merge the PR
    pr = repo.create_pull(
        title=f"Guardian: Merge '{source_branch}' → '{target_branch}'",
        body=f"Automated PR by GitHub Guardian.\n\n"
             f"- Conflicts found: {conflict_results['total_conflicts']}\n"
             f"- AI resolved: {len(conflict_results['ai_fixed'])}\n"
             f"- Unfixable: {len(conflict_results['ai_failed'])}",
        head=source_branch,
        base=target_branch,
    )

    try:
        merge_status = pr.merge(merge_method="squash")
        merged = merge_status.merged
    except GithubException as ge:
        return {
            "success": False,
            "merged": False,
            "reason": "merge_failed",
            "message": str(ge.data),
            "pr_url": pr.html_url,
            "conflict_results": conflict_results,
        }

    return {
        "success": True,
        "merged": merged,
        "pr_url": pr.html_url,
        "source_branch": source_branch,
        "target_branch": target_branch,
        "conflict_results": conflict_results,
        "message": f"Successfully merged '{source_branch}' into '{target_branch}'!" +
                   (f" AI fixed {len(conflict_results['ai_fixed'])} conflict(s)." if conflict_results['ai_fixed'] else ""),
    }


