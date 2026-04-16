import httpx
import json

async def check_dependency_confusion(package_json_content: str):
    """
    Scans a package.json for potential dependency confusion risks.
    Identifies packages that look internal but are not protected.
    """
    findings = []
    try:
        data = json.loads(package_json_content)
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        
        async with httpx.AsyncClient() as client:
            for pkg, version in deps.items():
                # Potential internal package indicators: @company scope or specific keywords
                if pkg.startswith('@') or any(k in pkg for k in ['internal', 'private', 'corp']):
                    # Check if it exists on public NPM
                    res = await client.get(f"https://registry.npmjs.org/{pkg}")
                    if res.status_code == 404:
                        findings.append({
                            "package": pkg,
                            "type": "Dependency Confusion Risk",
                            "severity": "HIGH",
                            "explanation": f"Package '{pkg}' looks internal but is NOT registered on NPM. An attacker could claim this name to inject malicious code into your builds."
                        })
    except:
        pass
    return findings
