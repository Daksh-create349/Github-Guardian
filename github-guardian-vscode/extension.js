const vscode = require('vscode');

// ──────────────────────────────────────────────────────────────────────────────
// PATTERNS — enterprise-grade, parity with Python CLI/backend engines
// ──────────────────────────────────────────────────────────────────────────────

const SECRET_PATTERNS = {
    "AWS Access Key ID": /AKIA[0-9A-Z]{16}/g,
    "AWS Secret Key": /aws_secret_access_key\s*[:=]\s*["']?([A-Za-z0-9/+=]{40})["']?/ig,
    "GitHub Token": /gh[pousr]_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z]{82}/g,
    "Slack Webhook": /https:\/\/hooks\.slack\.com\/services\/T[0-9A-Z]{8}\/B[0-9A-Z]{8}\/[0-9a-zA-Z]{24}/g,
    "Slack Token": /xox[bapr]-[0-9a-zA-Z]{10,48}/g,
    "Stripe API Key": /[rs]k_(?:live|test)_[0-9a-zA-Z]{24,32}/g,
    "Google API Key": /AIza[0-9A-Za-z\-_]{35}/g,
    "OpenAI API Key": /sk-[a-zA-Z0-9]{20,}/g,
    "Twilio Account SID": /AC[0-9a-fA-F]{32}/g,
    "Twilio Auth Token": /twilio_auth_token\s*[:=]\s*["']?([0-9a-fA-F]{32})["']?/ig,
    "Discord Webhook": /https:\/\/discord(?:app)?\.com\/api\/webhooks\/[0-9]+\/[0-9a-zA-Z_-]+/g,
    "Discord Bot Token": /[MN][A-Za-z0-9_]{23}\.[A-Za-z0-9_]{6}\.[A-Za-z0-9_]{27}/g,
    "Telegram Bot Token": /[0-9]{9,10}:[a-zA-Z0-9_-]{35}/g,
    // Heroku removed — standard UUID regex causes too many false positives
    "Mailgun API Key": /key-[0-9a-zA-Z]{32}/g,
    "SendGrid API Key": /SG\.[0-9a-zA-Z_-]{22}\.[0-9a-zA-Z_-]{43}/g,
    "Facebook Access Token": /EAACEdEose0c[0-9A-Za-z]+/g,
    "Database URL": /(?:mongodb(?:\+srv)?|postgres|postgresql|mysql|mssql|redis):\/\/[^:\s]+:[^@\s]+@[^@\s]+/g,
    "Private Key": /-----BEGIN (?:RSA |OPENSSH |DSA |EC |PGP )?PRIVATE KEY-----/g,
    "JWT": /eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}/g,
    "NPM Token": /npm_[0-9a-zA-Z]{36}/g
};

const GENERIC_ASSIGNMENT_PATTERN = /\b['"]?([a-z0-9_\-\.]*(?:key|secret|token|password|passwd|pw|auth|cred|pass)[a-z0-9_\-\.]*)['"]?\s*[:=]\s*['"]([a-zA-Z0-9_\-\.\/\+=]{16,})['"]/i;

const SAST_PATTERNS = {
    "SQL Injection (Raw Query)": /\.execute\(\s*['"].*['"]\s*%\s*/g,
    "Insecure Rendering (XSS)": /dangerouslySetInnerHTML/g,
    "Hardcoded Auth/Secret": /password\s*=\s*['"][^'"]+['"]/g
};

// ──────────────────────────────────────────────────────────────────────────────
// EXCLUSIONS
// ──────────────────────────────────────────────────────────────────────────────

const IGNORED_EXTENSIONS = new Set([
    "png", "jpg", "jpeg", "gif", "svg", "ico", "webp", "bmp",
    "pdf", "zip", "gz", "tar", "7z", "rar",
    "pyc", "pyo", "exe", "dll", "so", "dylib", "o", "a", "class",
    "woff", "woff2", "ttf", "eot", "otf",
    "tldr", "drawio", "map",
    "mp3", "mp4", "mov", "wav", "avi", "mkv", "flac", "ogg",
    "db", "sqlite", "sqlite3"
]);

const IGNORED_FILENAMES = new Set([
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "cargo.lock", "composer.lock",
    "gemfile.lock", "go.sum"
]);

const IGNORED_PATH_SEGMENTS = /[/\\](?:node_modules|\.git|venv|\.venv|build_env|__pycache__|\.next|\.nuxt|\.cache|coverage)[/\\]/;

// ──────────────────────────────────────────────────────────────────────────────
// ENTROPY
// ──────────────────────────────────────────────────────────────────────────────

function calculateEntropy(str) {
    if (!str) return 0;
    const frequencies = {};
    for (const char of str) {
        frequencies[char] = (frequencies[char] || 0) + 1;
    }
    let entropy = 0;
    const len = str.length;
    for (const char in frequencies) {
        const p = frequencies[char] / len;
        entropy -= p * Math.log2(p);
    }
    return entropy;
}

// ──────────────────────────────────────────────────────────────────────────────
// CORE SCANNER — operates on a single line of text
// ──────────────────────────────────────────────────────────────────────────────

function scanLine(line, entropyThreshold = 3.2) {
    const findings = [];
    let matchedAny = false;

    // 1. Specific secret patterns
    for (const [name, regex] of Object.entries(SECRET_PATTERNS)) {
        regex.lastIndex = 0;
        let match;
        while ((match = regex.exec(line)) !== null) {
            matchedAny = true;
            findings.push({
                type: 'SECRET LEAK',
                name,
                start: match.index,
                end: match.index + match[0].length,
                value: match[0]
            });
        }
    }

    // 2. Generic high-entropy assignment fallback
    if (!matchedAny) {
        const genMatch = GENERIC_ASSIGNMENT_PATTERN.exec(line);
        if (genMatch) {
            const varName = genMatch[1];
            const secretValue = genMatch[2];
            if (calculateEntropy(secretValue) >= entropyThreshold) {
                const startChar = line.indexOf(secretValue);
                findings.push({
                    type: 'SECRET LEAK',
                    name: `High-Entropy Secret (${varName})`,
                    start: startChar,
                    end: startChar + secretValue.length,
                    value: secretValue
                });
            }
        }
    }

    // 3. SAST / semantic vulnerabilities
    for (const [name, regex] of Object.entries(SAST_PATTERNS)) {
        regex.lastIndex = 0;
        let match;
        while ((match = regex.exec(line)) !== null) {
            findings.push({
                type: 'SAST VULN',
                name,
                start: match.index,
                end: match.index + match[0].length,
                value: match[0]
            });
        }
    }

    return findings;
}

// ──────────────────────────────────────────────────────────────────────────────
// VS CODE INTEGRATION
// ──────────────────────────────────────────────────────────────────────────────

let diagnosticCollection;
let changeTimeout;

function activate(context) {
    diagnosticCollection = vscode.languages.createDiagnosticCollection('github-guardian');
    context.subscriptions.push(diagnosticCollection);

    // Helper: read config fresh every time (picks up runtime changes)
    function getConfig() {
        return vscode.workspace.getConfiguration('github-guardian');
    }

    // Scan active file on startup
    if (vscode.window.activeTextEditor && getConfig().get('enable')) {
        scanDocument(vscode.window.activeTextEditor.document);
    }

    // Scan on active editor change
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor && getConfig().get('enable')) {
                scanDocument(editor.document);
            }
        })
    );

    // Scan on type (de-bounced 500ms)
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(event => {
            const cfg = getConfig();
            if (cfg.get('enable') && cfg.get('enableOnType')) {
                if (changeTimeout) clearTimeout(changeTimeout);
                changeTimeout = setTimeout(() => {
                    scanDocument(event.document);
                }, 500);
            }
        })
    );

    // Scan on save
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(document => {
            const cfg = getConfig();
            if (cfg.get('enable') && cfg.get('enableOnSave')) {
                scanDocument(document);
            }
        })
    );

    // Clear diagnostics when a file is closed
    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument(document => {
            diagnosticCollection.delete(document.uri);
        })
    );

    // Workspace Scan command
    context.subscriptions.push(
        vscode.commands.registerCommand('github-guardian.scanWorkspace', async () => {
            if (!getConfig().get('enable')) {
                vscode.window.showWarningMessage("🛡️ GitHub Guardian is currently disabled.");
                return;
            }

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "🛡️ GitHub Guardian: Scanning Workspace…",
                cancellable: true
            }, async (progress, cancelToken) => {
                const files = await vscode.workspace.findFiles(
                    '**/*',
                    '{**/node_modules/**,**/venv/**,**/.venv/**,**/.git/**,**/build_env/**,**/__pycache__/**,**/.next/**,**/coverage/**}'
                );
                let totalLeaks = 0;
                let scanned = 0;
                for (const file of files) {
                    if (cancelToken.isCancellationRequested) break;
                    try {
                        const doc = await vscode.workspace.openTextDocument(file);
                        totalLeaks += scanDocument(doc);
                    } catch (_) {
                        // binary / large files — skip silently
                    }
                    scanned++;
                    progress.report({ increment: (scanned / files.length) * 100, message: `${scanned}/${files.length} files` });
                }
                if (totalLeaks === 0) {
                    vscode.window.showInformationMessage("🛡️ GitHub Guardian: Workspace is clean — no secrets detected!");
                } else {
                    vscode.window.showWarningMessage(`🛡️ GitHub Guardian: Found ${totalLeaks} issue(s). Check the Problems tab.`);
                }
            });
        })
    );

    // Quick Fix code actions
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            [{ scheme: 'file' }, { scheme: 'untitled' }],
            new GuardianCodeActionProvider(),
            { providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] }
        )
    );

    // Status bar item
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
    statusBar.text = "$(shield) Guardian";
    statusBar.tooltip = "GitHub Guardian — Click to scan workspace";
    statusBar.command = 'github-guardian.scanWorkspace';
    statusBar.show();
    context.subscriptions.push(statusBar);
}

// ──────────────────────────────────────────────────────────────────────────────
// DOCUMENT SCANNER
// ──────────────────────────────────────────────────────────────────────────────

function scanDocument(document) {
    const docUri = document.uri;
    if (docUri.scheme !== 'file' && docUri.scheme !== 'untitled') return 0;

    const filePath = docUri.fsPath;

    if (docUri.scheme === 'file') {
        // Ignore dependency / build / environment paths
        if (IGNORED_PATH_SEGMENTS.test(filePath)) return 0;

        // Ignore binary / asset extensions
        const dotIdx = filePath.lastIndexOf('.');
        if (docUri.scheme === 'file' && dotIdx !== -1) {
            const ext = filePath.slice(dotIdx + 1).toLowerCase();
            if (IGNORED_EXTENSIONS.has(ext)) return 0;
        }

        // Ignore lockfiles
        const filename = filePath.split(/[/\\]/).pop().toLowerCase();
        if (IGNORED_FILENAMES.has(filename)) return 0;
    }

    const diagnostics = [];
    const text = document.getText();
    const lines = text.split(/\r?\n/);

    const entropyThreshold = vscode.workspace.getConfiguration('github-guardian').get('entropyThreshold') || 3.2;

    for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
        const findings = scanLine(lines[lineIdx], entropyThreshold);

        for (const finding of findings) {
            const range = new vscode.Range(lineIdx, finding.start, lineIdx, finding.end);
            const isSecret = finding.type !== 'SAST VULN';
            const severity = isSecret ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning;
            const icon = isSecret ? '🚨' : '⚠️';
            const message = `${icon} GitHub Guardian: [${finding.type}] ${finding.name}`;

            const diagnostic = new vscode.Diagnostic(range, message, severity);
            diagnostic.code = isSecret ? 'secret-leak' : 'sast-vuln';
            diagnostic.source = 'GitHub Guardian';
            diagnostics.push(diagnostic);
        }
    }

    diagnosticCollection.set(docUri, diagnostics);
    return diagnostics.length;
}

// ──────────────────────────────────────────────────────────────────────────────
// QUICK FIX PROVIDER
// ──────────────────────────────────────────────────────────────────────────────

class GuardianCodeActionProvider {
    provideCodeActions(document, _range, context) {
        const codeActions = [];
        for (const diagnostic of context.diagnostics) {
            if (diagnostic.source !== 'GitHub Guardian') continue;

            const codeValue = (diagnostic.code && typeof diagnostic.code === 'object') ? diagnostic.code.value : diagnostic.code;
            if (codeValue === 'secret-leak') {
                // Quick Fix 1: Redact the secret
                const redactAction = new vscode.CodeAction(
                    "🛡️ Redact secret (replace with placeholder)",
                    vscode.CodeActionKind.QuickFix
                );
                redactAction.diagnostics = [diagnostic];
                redactAction.edit = new vscode.WorkspaceEdit();
                redactAction.edit.replace(document.uri, diagnostic.range, '"REDACTED_BY_GUARDIAN"');
                redactAction.isPreferred = true;
                codeActions.push(redactAction);

                // Quick Fix 2: Move to environment variable
                const envAction = new vscode.CodeAction(
                    "🔐 Replace with process.env reference",
                    vscode.CodeActionKind.QuickFix
                );
                envAction.diagnostics = [diagnostic];
                envAction.edit = new vscode.WorkspaceEdit();
                envAction.edit.replace(document.uri, diagnostic.range, 'process.env.SECRET_VALUE');
                codeActions.push(envAction);
            }
        }
        return codeActions;
    }
}

// ──────────────────────────────────────────────────────────────────────────────

function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
        diagnosticCollection.dispose();
    }
}

module.exports = {
    activate,
    deactivate,
    calculateEntropy,
    scanLine,
    SECRET_PATTERNS,
    GENERIC_ASSIGNMENT_PATTERN,
    SAST_PATTERNS
};
