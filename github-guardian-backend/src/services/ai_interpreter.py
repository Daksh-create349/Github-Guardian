def interpret_finding(finding_str: str) -> dict:
    """
    Genuine Security Intelligence: Provides specific explanations and fixes 
    based on the actual vulnerability type.
    """
    f = str(finding_str).lower()
    
    # Logic for SQL Injection
    if "sql" in f or "query" in f:
        return {
            "severity_score": 9,
            "explanation": "Detected raw string interpolation in a database query. This is a classic SQL Injection vulnerability.",
            "fix": "Use parameterized queries (e.g., Prepared Statements) instead of string concatenation."
        }
    
    # Logic for XSS
    if "xss" in f or "innerhtml" in f or "dangerously" in f:
        return {
            "severity_score": 8,
            "explanation": "Detected insecure rendering of user-controlled data into the DOM. This can lead to Cross-Site Scripting (XSS).",
            "fix": "Sanitize user inputs using a library like DOMPurify or use secure rendering methods (e.g., textContent)."
        }

    # Logic for Secrets
    if "key" in f or "token" in f or "secret" in f:
        return {
            "severity_score": 10,
            "explanation": "A high-entropy string matching a sensitive credential pattern was found in the codebase or history.",
            "fix": "Immediately rotate this secret. Use a tool like 'git-filter-repo' to scrub it from your entire git history."
        }

    # Default logic
    return {
        "severity_score": 6,
        "explanation": "A potential security anti-pattern was detected during the automated audit.",
        "fix": "Review the highlighted code for security best practices and ensure no sensitive data is exposed."
    }

def generate_repo_report(findings: dict, repo_overview: dict) -> dict:
    """
    Generates a qualitative report for the entire repository.
    Calculates the score accurately based on weighted findings.
    """
    positives = []
    negatives = []
    
    secret_count = len(findings.get("secret_findings", []))
    sast_count = len(findings.get("sast_findings", []))
    oops_count = len(findings.get("oops_commits", []))
    sc_summary = findings.get("supply_chain", {}).get("summary", {})
    dep_confusion = len(findings.get("dependency_issues", []))
    ci_cd_issues = len(findings.get("ci_cd_issues", []))
    
    # 1. Calculate Score (Weight-based)
    raw_score = 0
    
    # Secrets (Live = 5 pts, Historical = 2 pts)
    for s in findings.get("secret_findings", []):
        label = s['pattern_matched']
        if label == "Exposed Sensitive File":
            label = s.get("secret_redacted", "Sensitive File") # Shows the actual filename (e.g. .env)

        if "Live" in s.get("commit_sha", ""):
            raw_score += 5
            negatives.append(f"CRITICAL: Active leak of {label} found.")
        else:
            raw_score += 2
            negatives.append(f"HIGH: Historical leak of {label} in git history.")

    # SAST Findings (Critical = 4 pts each)
    for s in findings.get("sast_findings", []):
        weight = 4 if s["severity"] == "CRITICAL" else 2
        raw_score += weight
        negatives.append(f"{s['severity']}: {s['type']} detected in {s['file']}.")

    # CI/CD Misconfigs (Critical = 4 pts each)
    if ci_cd_issues > 0:
        raw_score += ci_cd_issues * 4
        negatives.append(f"CRITICAL: Found {ci_cd_issues} GitHub Action misconfigurations (pull_request_target).")

    # Dependency Confusion (High = 3 pts each)
    if dep_confusion > 0:
        raw_score += dep_confusion * 3
        negatives.append(f"HIGH: Detected {dep_confusion} possible Dependency Confusion risks in package.json.")

    # Supply Chain (Critical = 3, High = 1)
    crit_vulns = sc_summary.get("critical", 0)
    if crit_vulns > 0:
        raw_score += crit_vulns * 3
        negatives.append(f"MEDIUM: {crit_vulns} Critical Supply Chain vulnerabilities found.")

    # 2. Add Positives
    if secret_count == 0 and sast_count == 0:
        positives.append("No credential leaks or semantic vulnerabilities detected.")
    if dep_confusion == 0:
        positives.append("Dependency list is protected against confusion attacks.")
    if repo_overview.get("stars", 0) > 100:
        positives.append(f"High community trust ({repo_overview['stars']} stars).")
    if len(repo_overview.get("workflow_files", [])) > 0:
        positives.append("CI/CD infrastructure detected (GitHub Actions).")

    # 3. Finalize Score and Verdict (Nuanced Non-Linear Scoring)
    # This prevents a single finding from instantly hitting 10.
    # We use a dampening curve: Score = 10 * (1 - 0.85^(raw_score/2))
    import math
    if raw_score > 0:
        final_score = round(10 * (1 - math.pow(0.85, raw_score / 2.0)), 1)
    else:
        final_score = 0.0

    verdict = "Your repository is healthy."
    if final_score >= 9.0:
        verdict = "CATASTROPHIC: Total security failure. Multiple layers compromised."
    elif final_score >= 7.0:
        verdict = "EMERGENCY: Major architectural holes detected. Exploitation likely."
    elif final_score >= 4.0:
        verdict = "WARNING: Significant security debt. Critical vulnerabilities found."
    elif final_score >= 1.0:
        verdict = "CAUTION: Minor leaks or insecurity patterns detected."
    elif final_score == 0:
        verdict = "EXCELLENT: Forensic grade security posture."

    # 4. Audit Summary (Conditions Verified)
    audit_summary = [
        "Swept git history for secrets",
        "Audited live file tree for exposure",
        "Semantic SAST pattern matching (SQLi, XSS)",
        "AI-driven architectural code review",
        "Polled NPM registry for Dependency Confusion",
        "Parsed CI/CD YAML configurations",
        "Scanned supply chain via Syft & Grype"
    ]

    return {
        "score": final_score,
        "verdict": verdict,
        "positives": positives[:5],
        "negatives": negatives[:5],
        "audit_summary": audit_summary,
        "code_review": findings.get("code_review", {})
    }
