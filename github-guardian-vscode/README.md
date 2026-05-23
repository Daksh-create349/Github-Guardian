# GitHub Guardian VS Code Extension

🛡️ **GitHub Guardian** is a real-time, zero-dependency forensic security audit assistant and secret shield for VS Code.

It runs locally on your machine, highlighting exposed secrets and insecure patterns inline in the editor and aggregating them in the **Problems** tab.

---

## Features

1. **Inline Scanning**: Instantly flags exposed API keys and security issues directly in your editor as you open, type, or save.
2. **Problems Panel Integration**: Aggregates all issues in the Workspace Problems panel for easy navigation.
3. **Enterprise-Grade platform detections**: Includes signatures for AWS, GitHub, Slack, Stripe, OpenAI, Google, Twilio, Databases, JWT, NPM, SSH Private Keys, etc.
4. **Dynamic Shannon-Entropy Engine**: Analyzes generic variable assignments (`password = "..."`) using Shannon Entropy calculations, warning you about custom keys while preventing noise.
5. **Quick Fix Redaction**: Provides editor lightbulb actions to automatically redact flagged secrets with one click.
6. **Workspace Scan**: Offers a command to scan your entire workspace.

---

## Extension Settings

This extension contributes the following settings:

* `github-guardian.enable`: Toggle real-time scanning (default: `true`).
* `github-guardian.enableOnSave`: Scan documents automatically when saving (default: `true`).
* `github-guardian.enableOnType`: Scan and update diagnostics as you edit/type (default: `true`).
* `github-guardian.entropyThreshold`: Entropy value threshold for generic secrets (default: `3.2`).

---

## Commands

* `GitHub Guardian: Scan Workspace for Secrets`: Searches all files in the current workspace (excluding `venv`, `node_modules`, and build artifacts) and registers findings.

---

## Manual Testing & Development

To test the extension:
1. Open this repository inside VS Code.
2. Open the file `github-guardian-vscode/extension.js`.
3. Press `F5` (or go to Run > Start Debugging). This launches a new **Extension Development Host** window.
4. Open any file in the Extension Development Host window.
5. Type an exposed key (e.g., `aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"`) and see it underlined in red immediately!
