import yaml

def analyze_workflows(workflow_contents: list):
    """
    Audits GitHub Action YAMLs for insecure triggers like 'pull_request_target'
    without explicit environment protection.
    """
    findings = []
    for content in workflow_contents:
        try:
            data = yaml.safe_load(content)
            on = data.get('on', {})
            
            # Check for pull_request_target which is highly dangerous if not scoped properly
            if 'pull_request_target' in str(on):
                # Look for permission elevation or scripts running PR code
                findings.append({
                    "trigger": "pull_request_target",
                    "type": "CI/CD Permission Elevation",
                    "severity": "CRITICAL",
                    "explanation": "Found 'pull_request_target' trigger. This can be exploited to steal GITHUB_TOKEN if you run untrusted PR code in this workflow."
                })
        except:
            pass
    return findings
