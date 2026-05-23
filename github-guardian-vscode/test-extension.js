const assert = require('assert');

// 1. Mock the VS Code API
const mockVscode = {
    Range: class {
        constructor(sl, sc, el, ec) { this.sl = sl; this.sc = sc; this.el = el; this.ec = ec; }
    },
    Diagnostic: class {
        constructor(range, message, severity) { this.range = range; this.message = message; this.severity = severity; }
    },
    DiagnosticSeverity: { Error: 0, Warning: 1, Information: 2, Hint: 3 },
    CodeActionKind: { QuickFix: 'quickfix' },
    StatusBarAlignment: { Left: 1, Right: 2 },
    ProgressLocation: { Notification: 15 },
    WorkspaceEdit: class { replace() {} },
    CodeAction: class { constructor(title, kind) { this.title = title; this.kind = kind; } },
    languages: {
        createDiagnosticCollection: () => ({ clear() {}, dispose() {}, set() {}, delete() {} }),
        registerCodeActionsProvider: () => ({ dispose() {} })
    },
    commands: { registerCommand: () => ({ dispose() {} }) },
    window: {
        activeTextEditor: null,
        onDidChangeActiveTextEditor: () => ({ dispose() {} }),
        createStatusBarItem: () => ({ show() {}, dispose() {} })
    },
    workspace: {
        getConfiguration: () => ({
            get: (key) => key === 'entropyThreshold' ? 3.2 : true
        }),
        onDidChangeTextDocument: () => ({ dispose() {} }),
        onDidSaveTextDocument: () => ({ dispose() {} }),
        onDidCloseTextDocument: () => ({ dispose() {} })
    }
};

// 2. Intercept require('vscode')
const Module = require('module');
const origResolve = Module._resolveFilename;
Module._resolveFilename = function (req, ...args) {
    if (req === 'vscode') return 'vscode';
    return origResolve.call(this, req, ...args);
};
require.cache['vscode'] = { id: 'vscode', filename: 'vscode', exports: mockVscode, loaded: true };

// 3. Load extension
const ext = require('./extension.js');

// ─── Tests ───────────────────────────────────────────────────────────────────

function run() {
    console.log("Running GitHub Guardian Extension tests…\n");

    // --- Specific secrets ---
    check('AWS Access Key ID',
        ext.scanLine('key = "AKIAIOSFODNN7EXAMPLE"'),
        f => f.name === 'AWS Access Key ID');

    check('AWS Secret Key',
        ext.scanLine('aws_secret_access_key = "wJalrXUtn' + 'FEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'),
        f => f.name === 'AWS Secret Key');

    check('GitHub Token',
        ext.scanLine('token = "ghp_' + '123456789012345678901234567890123456"'),
        f => f.name === 'GitHub Token');

    check('Slack Webhook',
        ext.scanLine('url = "https://hooks.slack.com/services/' + 'T12345678/' + 'B12345678/' + 'aBcDeFgHiJkLmNoPqRsTuVwX"'),
        f => f.name === 'Slack Webhook');

    check('Slack Token',
        ext.scanLine('token = "xoxb-' + '1234567890-123456789012-aBcDeFgHiJkLmNoPqRsTuVwX"'),
        f => f.name === 'Slack Token');

    check('Stripe API Key',
        ext.scanLine('key = "sk_live_' + '123456789012345678901234"'),
        f => f.name === 'Stripe API Key');

    check('Google API Key',
        ext.scanLine('key = "AIzaSyA' + '1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q"'),
        f => f.name === 'Google API Key');

    check('OpenAI API Key',
        ext.scanLine('key = "sk-' + '1234567890abcdef1234567890abcdef12345678"'),
        f => f.name === 'OpenAI API Key');

    check('Twilio Account SID',
        ext.scanLine('sid = "AC' + '1234567890abcdef1234567890abcdef"'),
        f => f.name === 'Twilio Account SID');

    check('Database URL',
        ext.scanLine('conn = "postgres://user:super_secret@localhost:5432/mydb"'),
        f => f.name === 'Database URL');

    check('Private Key',
        ext.scanLine('-----BEGIN RSA PRIVATE KEY-----'),
        f => f.name === 'Private Key');

    check('SendGrid API Key',
        ext.scanLine('key = "SG.1234567890abcdefghijkl.1234567890abcdefghijklmnopqrstuvwxyz1234567"'),
        f => f.name === 'SendGrid API Key');

    // --- High-entropy fallback ---
    check('High-Entropy Secret (flags)',
        ext.scanLine('custom_auth_token = "4a8e2b9c7d8e9f0a2b3c4d5e6f7a8b9c"'),
        f => f.name.includes('High-Entropy Secret'));

    check('Low-entropy password (no false positive)',
        ext.scanLine('safe_password = "passwordpassword"'),
        f => f.name.includes('High-Entropy Secret'),
        true /* expect NONE */);

    check('Non-secret variable name (no false positive)',
        ext.scanLine('some_random_text = "4a8e2b9c7d8e9f0a2b3c4d5e6f7a8b9c"'),
        f => f.name.includes('High-Entropy Secret'),
        true /* expect NONE */);

    // --- UUIDs should NOT fire (Heroku removed) ---
    check('UUID in config (no false positive)',
        ext.scanLine('"id": "816ab0fc-1d04-41a5-9c62-b381cf4185b8"'),
        f => f.type === 'SECRET LEAK',
        true /* expect NONE */);

    // --- SAST ---
    check('SQL Injection',
        ext.scanLine('db.execute("SELECT * FROM users WHERE name = %s" % username)'),
        f => f.name === 'SQL Injection (Raw Query)');

    check('XSS dangerouslySetInnerHTML',
        ext.scanLine('<div dangerouslySetInnerHTML={{__html: data}} />'),
        f => f.name === 'Insecure Rendering (XSS)');

    // --- Entropy function ---
    assert.ok(ext.calculateEntropy('aaaa') < 1, 'Low entropy string should be < 1');
    assert.ok(ext.calculateEntropy('4a8e2b9c7d') > 3, 'High entropy string should be > 3');
    console.log('  ✓ Entropy calculation');

    console.log('\n✅ All tests passed!');
}

function check(label, results, predicate, expectNone = false) {
    const found = results.some(predicate);
    if (expectNone) {
        assert.ok(!found, `FAIL: "${label}" — should NOT have matched but did`);
    } else {
        assert.ok(found, `FAIL: "${label}" — expected match not found`);
    }
    console.log(`  ✓ ${label}`);
}

run();
