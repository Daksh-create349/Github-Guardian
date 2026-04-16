import subprocess
import tempfile
import json
import os

def generate_sbom_and_scan(owner: str, repo_name: str):
    # This now runs natively on your CPU using 'syft' and 'grype' binaries.
    # No Docker required.
    
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    with tempfile.TemporaryDirectory() as td:
        repo_url = f"https://github.com/{owner}/{repo_name}.git"
        # Shallow clone to speed up native processing
        subprocess.run(["git", "clone", "--depth", "1", repo_url, td], capture_output=True, check=False)
        
        sbom_path = os.path.join(td, "sbom.json")
        
        try:
            # 1. Run native 'syft' to generate SBOM into local file
            # Requirements: brew install syft
            subprocess.run([
                "syft", "dir:" + td, 
                "-o", "cyclonedx-json", 
                "--file", sbom_path
            ], capture_output=True, check=False)
            
            # 2. Run native 'grype' on that SBOM
            # Requirements: brew install grype
            res_grype = subprocess.run([
                "grype", "sbom:" + sbom_path, 
                "-o", "json"
            ], capture_output=True, text=True, check=False)
            
            if res_grype.stdout:
                vuln_data = json.loads(res_grype.stdout)
                matches = vuln_data.get("matches", [])
                for m in matches:
                    sev = m.get("vulnerability", {}).get("severity", "").lower()
                    if sev in summary:
                        summary[sev] += 1
                        
        except Exception as e:
            # Fallback if binaries are missing
            summary = {"error": f"Native tools syft/grype not found. Run 'brew install syft grype'. Details: {str(e)}"}
            
    return {
        "summary": summary,
        "sbom_path": f"/tmp/{owner}_{repo_name}_sbom.json"
    }
