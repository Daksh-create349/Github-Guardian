import { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { API_AUTH_LOGIN_URL } from '../api/config';
import { useAuth } from '../context/AuthContext';
import {
  Folder as FolderIcon,
  UploadFile as UploadFileIcon,
  Security as SecurityIcon,
  RocketLaunch as RocketIcon,
  GitHub as GitHubIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
  Lock as LockIcon,
  Block as BlockIcon,
  Lightbulb as BulbIcon,
  Celebration as PartyIcon,
  Link as LinkIcon,
  Add as AddIcon,
  ErrorOutline as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  HourglassEmpty as HourglassIcon,
  Info as InfoIcon,
  Code as CodeIcon,
  Image as ImageIcon,
  Description as DocIcon,
  VpnKey as KeyIcon,
  Archive as ArchiveIcon,
  ArrowForward as ArrowRightIcon,
  ArrowBack as ArrowLeftIcon
} from '@mui/icons-material';

// ─── File type icon helper ────────────────────────────────────────────────────
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  const codeExts = new Set(['js', 'jsx', 'ts', 'tsx', 'py', 'rb', 'go', 'rs', 'html', 'css', 'scss', 'sh', 'bash']);
  const dataExts = new Set(['json', 'yaml', 'yml', 'toml']);
  const imgExts = new Set(['png', 'jpg', 'jpeg', 'gif', 'svg']);
  const docExts = new Set(['md', 'txt', 'pdf']);
  const archiveExts = new Set(['zip', 'tar', 'gz']);
  const keyExts = new Set(['pem', 'key']);

  if (filename.startsWith('.env')) return <LockIcon fontSize="inherit" />;
  if (codeExts.has(ext)) return <CodeIcon fontSize="inherit" />;
  if (dataExts.has(ext)) return <DocIcon fontSize="inherit" />;
  if (imgExts.has(ext)) return <ImageIcon fontSize="inherit" />;
  if (docExts.has(ext)) return <DocIcon fontSize="inherit" />;
  if (archiveExts.has(ext)) return <ArchiveIcon fontSize="inherit" />;
  if (keyExts.has(ext)) return <KeyIcon fontSize="inherit" />;
  
  return <FileIcon fontSize="inherit" />;
};

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};

// ─── Frontend sensitive detection (mirrors backend) ──────────────────────────
const SENSITIVE_NAMES = new Set([
  '.env', '.env.local', '.env.production', '.env.development',
  '.env.staging', '.env.test', 'id_rsa', 'id_rsa.pub',
  'id_ed25519', 'secrets.json', 'credentials.json',
]);
const SENSITIVE_EXTS = new Set(['.pem', '.key', '.p12', '.pfx', '.crt', '.cer', '.ppk']);
const SENSITIVE_FOLDERS = new Set([
  'node_modules', 'venv', '.venv', 'env', 'ENV',
  '__pycache__', 'dist', 'build', '.git', '.next',
]);

function getSensitivityInfo(filename) {
  const parts = filename.replace(/\\/g, '/').split('/');
  const base = parts[parts.length - 1];
  const ext = '.' + base.split('.').pop().toLowerCase();

  if (SENSITIVE_NAMES.has(base) || base.startsWith('.env'))
    return { type: 'secret', label: 'SECRET', color: '#cf222e', icon: LockIcon };
  if (SENSITIVE_EXTS.has(ext))
    return { type: 'key', label: 'KEY/CERT', color: '#8250df', icon: KeyIcon };
  for (let i = 0; i < parts.length - 1; i++) {
    if (SENSITIVE_FOLDERS.has(parts[i]))
      return { type: 'excluded', label: 'EXCLUDED', color: '#9a6700', icon: BlockIcon };
  }
  return null;
}

// ─── Step config ──────────────────────────────────────────────────────────────
const STEPS = [
  { id: 1, label: 'NAME', title: 'Name Your Repository', icon: FolderIcon },
  { id: 2, label: 'FILES', title: 'Add Your Files', icon: UploadFileIcon },
  { id: 3, label: 'REVIEW', title: 'Review & Protect', icon: SecurityIcon },
  { id: 4, label: 'LAUNCH', title: 'Commit & Push', icon: RocketIcon },
];

// ─── Explanation boxes ────────────────────────────────────────────────────────
const EXPLANATIONS = {
  1: {
    icon: FolderIcon,
    what: 'What is a repository?',
    body: "A repository (or 'repo') is like a folder on GitHub that stores all your project files. Think of it as a cloud drive that also remembers every change you ever make. You need a unique name that no one else on GitHub has already used."
  },
  2: {
    icon: UploadFileIcon,
    what: 'How do I add files?',
    body: "Drag and drop your project files OR click 'Browse Files' to select them. You can add as many files as you want. Don't worry about secrets like .env files — we'll automatically protect them!"
  },
  3: {
    icon: SecurityIcon,
    what: 'What is a .gitignore?',
    body: "A .gitignore is a special file that tells GitHub 'never upload these files'. We auto-detected sensitive files like API keys, passwords, and huge folders like node_modules. We'll create this protection file automatically!"
  },
  4: {
    icon: RocketIcon,
    what: 'What is a commit & push?',
    body: "A 'commit' is like taking a snapshot of your code with a label. A 'push' uploads that snapshot to GitHub. Write a short message describing what this version does, then hit LAUNCH and we'll do everything else!"
  },
};

export default function GithubDesktopPage() {
  const navigate = useNavigate();
  const { user, loading, logout } = useAuth();
  const fileInputRef = useRef(null);
  const dropZoneRef = useRef(null);

  const [step, setStep] = useState(1);
  const [isDragging, setIsDragging] = useState(false);

  // Step 1
  const [repoName, setRepoName] = useState('');
  const [description, setDescription] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [nameStatus, setNameStatus] = useState(null); // null | 'checking' | {available, sanitized_name, suggestions, username}

  // Step 2
  const [files, setFiles] = useState([]);

  // Step 3
  const [commitMessage, setCommitMessage] = useState('');

  // Step 4
  const [pushStatus, setPushStatus] = useState('idle'); // idle | pushing | done | error
  const [pushResult, setPushResult] = useState(null);
  const [pushError, setPushError] = useState('');
  const [pushLog, setPushLog] = useState([]);

  // ── Name checking (debounced) ───────────────────────────────────────────────
  useEffect(() => {
    if (!repoName.trim()) { setNameStatus(null); return; }
    setNameStatus('checking');
    const timer = setTimeout(async () => {
      try {
        const { data } = await client.get(`/desktop/check-name/${encodeURIComponent(repoName.trim())}`);
        setNameStatus(data);
        if (data.available && !commitMessage) {
          setCommitMessage(`Initial commit — ${data.sanitized_name}`);
        }
      } catch {
        setNameStatus(null);
      }
    }, 700);
    return () => clearTimeout(timer);
  }, [repoName]);

  // ── File handling ───────────────────────────────────────────────────────────
  const addFiles = useCallback((newFileObjs) => {
    const processed = Array.from(newFileObjs).map((f) => ({
      id: `${f.name}-${f.size}-${Date.now()}`,
      name: f.webkitRelativePath || f.name,
      size: f.size,
      fileObj: f,
      sensitivity: getSensitivityInfo(f.webkitRelativePath || f.name),
    }));
    setFiles((prev) => {
      const existingNames = new Set(prev.map((p) => p.name));
      return [...prev, ...processed.filter((f) => !existingNames.has(f.name))];
    });
  }, []);

  const removeFile = (id) => setFiles((prev) => prev.filter((f) => f.id !== id));

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = (e) => { if (!dropZoneRef.current?.contains(e.relatedTarget)) setIsDragging(false); };

  // ── Push ────────────────────────────────────────────────────────────────────
  const handlePush = async () => {
    if (!nameStatus?.available) return;
    setPushStatus('pushing');
    setPushLog([]);

    const logStep = (msg) => setPushLog((prev) => [...prev, msg]);

    logStep('Scanning files for secrets...');
    await new Promise((r) => setTimeout(r, 600));
    logStep('Generating .gitignore protection file...');
    await new Promise((r) => setTimeout(r, 500));
    logStep(`Creating repository "${nameStatus.sanitized_name}" on GitHub...`);

    const formData = new FormData();
    formData.append('repo_name', nameStatus.sanitized_name);
    formData.append('description', description);
    formData.append('private', isPrivate.toString());
    formData.append('commit_message', commitMessage || `Initial commit — ${nameStatus.sanitized_name}`);

    const safeFiles = files.filter((f) => f.sensitivity?.type !== 'excluded');
    for (const f of safeFiles) {
      formData.append('files', f.fileObj, f.name);
    }

    try {
      logStep(`Uploading ${safeFiles.length} file(s)...`);
      const { data } = await client.post('/desktop/create-and-push', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });
      logStep(`Successfully pushed ${data.files_pushed} file(s)!`);
      logStep(`Repository is live at github.com/${nameStatus.username}/${nameStatus.sanitized_name}`);
      setPushResult(data);
      setPushStatus('done');
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Unknown error';
      logStep(`Push failed: ${msg}`);
      setPushError(msg);
      setPushStatus('error');
    }
  };

  // ── Computed stats ──────────────────────────────────────────────────────────
  const secrets = files.filter((f) => f.sensitivity?.type === 'secret');
  const excluded = files.filter((f) => f.sensitivity?.type === 'excluded');
  const keys = files.filter((f) => f.sensitivity?.type === 'key');
  const safe = files.filter((f) => !f.sensitivity);
  const canProceed1 = nameStatus?.available;
  const canProceed2 = files.length > 0;

  // ── Auth Guards ─────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'VT323', monospace", fontSize: '1.5rem' }}>
        <HourglassIcon sx={{ mr: 1 }} /> Loading...
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#fff', gap: 20, padding: 32, textAlign: 'center' }}>
        <LockIcon sx={{ fontSize: '4rem' }} />
        <div className="vt323" style={{ fontSize: '2.5rem', letterSpacing: 4 }}>SIGN IN REQUIRED</div>
        <div className="vt323" style={{ fontSize: '1.2rem', color: '#555', maxWidth: 500, lineHeight: 1.6 }}>
          GitHub Desktop uses <strong>YOUR</strong> GitHub account to create repositories.
          Sign in so repos are created on your account — not someone else's!
        </div>
        <button
          className="pixel-button primary"
          onClick={() => { window.location.href = API_AUTH_LOGIN_URL; }}
          style={{
            display: 'flex', alignItems: 'center', gap: 10, marginTop: 8
          }}
        >
          <GitHubIcon sx={{ fontSize: '1.5rem' }} /> SIGN IN WITH GITHUB
        </button>
        <button
          className="vt323"
          onClick={() => navigate('/')}
          style={{ border: 'none', background: 'none', fontSize: '1rem', color: '#888', cursor: 'pointer', textDecoration: 'underline' }}
        >
          <ArrowLeftIcon sx={{ fontSize: 16, verticalAlign: 'middle', mr: 0.5 }} /> Back to home
        </button>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#fff' }}>
      {/* Header */}
      <div style={{
        background: '#000', color: '#fff', padding: '16px 32px',
        display: 'flex', alignItems: 'center', gap: 16,
        borderBottom: '4px solid #0969DA',
      }}>
        <GitHubIcon sx={{ fontSize: '2.5rem' }} />
        <div>
          <div className="vt323" style={{ fontSize: '1.8rem', letterSpacing: 4 }}>GITHUB GUARDIAN DESKTOP</div>
          <div className="vt323" style={{ fontSize: '1rem', opacity: 0.7, letterSpacing: 2 }}>
            CREATE · PROTECT · PUSH — IN 4 EASY STEPS
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="pixel-border" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: '#000', borderColor: '#ffffff50', color: '#fff', boxShadow: 'none' }}>
            <img src={user.avatar_url} alt={user.username} style={{ width: 28, height: 28, borderRadius: '50%' }} />
            <span className="vt323" style={{ fontSize: '1rem', opacity: 0.9 }}>@{user.username}</span>
          </div>
          <button className="pixel-button" style={{ background: 'transparent', color: '#fff', borderColor: '#fff' }} onClick={logout}>LOGOUT</button>
          <button className="pixel-button" style={{ background: 'transparent', color: '#fff', borderColor: '#fff' }} onClick={() => navigate('/')}>BACK</button>
        </div>
      </div>

      {/* Step indicators */}
      <div style={{
        display: 'flex', gap: 0, borderBottom: '3px solid #000',
        background: '#F8F8F8',
      }}>
        {STEPS.map((s) => {
          const IconComponent = step > s.id ? CheckIcon : s.icon;
          return (
            <div key={s.id} className="vt323" style={{
              flex: 1, padding: '14px 8px', borderRight: '2px solid #000',
              background: step > s.id ? '#2da44e' : step === s.id ? '#0969DA' : '#F8F8F8',
              color: step >= s.id ? '#fff' : '#666',
              fontSize: '1.1rem', letterSpacing: 2,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              transition: 'all 0.2s',
            }}>
              <IconComponent fontSize="small" /> {s.label}
            </div>
          );
        })}
      </div>

      {/* Body */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 360px',
        minHeight: 'calc(100vh - 120px)',
      }}>
        {/* Main panel */}
        <div style={{ padding: '40px 48px', borderRight: '3px solid #000' }}>

          {/* ── STEP 1: NAME ── */}
          {step === 1 && (
            <>
              <div className="vt323" style={{ fontSize: '2.2rem', marginBottom: '8px', letterSpacing: 3 }}>
                STEP 1 — NAME YOUR REPOSITORY
              </div>
              <div className="vt323" style={{ color: '#666', fontSize: '1.1rem', marginBottom: '32px' }}>
                Give your project a unique name on GitHub.
              </div>

              <div className="pixel-border" style={{ padding: '24px', marginBottom: '16px', background: '#fff' }}>
                <label className="vt323" style={{ fontSize: '1.1rem', display: 'block', marginBottom: '8px' }}>
                  REPOSITORY NAME <span style={{ color: '#cf222e' }}>*</span>
                </label>
                <div style={{ display: 'flex', gap: 0 }}>
                  <input
                    className="vt323"
                    style={{
                      width: '100%', border: '3px solid #000', padding: '12px 16px',
                      fontSize: '1.3rem', outline: 'none', background: '#fff',
                      borderRight: 'none', flex: 1
                    }}
                    placeholder="my-awesome-project"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && canProceed1 && setStep(2)}
                  />
                  <div className="vt323" style={{
                    border: '3px solid #000', padding: '0 16px',
                    display: 'flex', alignItems: 'center', gap: '6px', background: '#F8F8F8',
                    fontSize: '1.1rem', whiteSpace: 'nowrap',
                  }}>
                    {nameStatus === 'checking' && <><HourglassIcon fontSize="small" /> CHECKING...</>}
                    {nameStatus?.available === true && <><CheckIcon fontSize="small" sx={{ color: '#2da44e' }} /> <span style={{ color: '#2da44e' }}>AVAILABLE</span></>}
                    {nameStatus?.available === false && <><CloseIcon fontSize="small" sx={{ color: '#cf222e' }} /> <span style={{ color: '#cf222e' }}>TAKEN</span></>}
                    {!repoName && <span style={{ opacity: 0.4 }}>TYPE A NAME</span>}
                  </div>
                </div>

                {nameStatus?.sanitized_name && nameStatus.sanitized_name !== repoName && (
                  <div className="vt323" style={{ marginTop: '8px', color: '#9a6700', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <InfoIcon fontSize="small" /> Will be saved as: <strong>{nameStatus.sanitized_name}</strong>
                    &nbsp;(spaces & special chars auto-fixed)
                  </div>
                )}

                {nameStatus?.available === false && nameStatus.suggestions?.length > 0 && (
                  <div style={{ marginTop: '16px' }}>
                    <div className="vt323" style={{ fontSize: '1rem', marginBottom: '8px', color: '#666' }}>
                      SUGGESTED ALTERNATIVES:
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {nameStatus.suggestions.map((s) => (
                        <button
                          key={s}
                          className="pixel-button primary"
                          style={{ fontSize: '1rem', padding: '6px 14px' }}
                          onClick={() => setRepoName(s)}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="pixel-border" style={{ padding: '24px', marginBottom: '16px', background: '#fff' }}>
                <label className="vt323" style={{ fontSize: '1.1rem', display: 'block', marginBottom: '8px' }}>
                  DESCRIPTION <span style={{ opacity: 0.5 }}>(optional)</span>
                </label>
                <input
                  className="vt323"
                  style={{
                    width: '100%', border: '3px solid #000', padding: '12px 16px',
                    fontSize: '1.3rem', outline: 'none', background: '#fff'
                  }}
                  placeholder="A cool project that does amazing things..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="pixel-border" style={{ padding: '24px', marginBottom: '16px', background: '#fff' }}>
                <div className="vt323" style={{ fontSize: '1.1rem', marginBottom: '16px' }}>VISIBILITY</div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    className="pixel-button"
                    style={{
                      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                      borderColor: !isPrivate ? '#2da44e' : '#000',
                      background: !isPrivate ? '#DCFCE7' : '#fff',
                      color: !isPrivate ? '#2da44e' : '#666'
                    }}
                    onClick={() => setIsPrivate(false)}
                  >
                    Public — Anyone can see this
                  </button>
                  <button
                    className="pixel-button"
                    style={{
                      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                      borderColor: isPrivate ? '#cf222e' : '#000',
                      background: isPrivate ? '#FEE2E2' : '#fff',
                      color: isPrivate ? '#cf222e' : '#666'
                    }}
                    onClick={() => setIsPrivate(true)}
                  >
                    <LockIcon fontSize="small" /> Private — Only you
                  </button>
                </div>
              </div>

              <button
                className="pixel-button primary"
                style={{
                  width: '100%', marginTop: '24px', display: 'flex', justifyContent: 'center', gap: 8,
                  opacity: canProceed1 ? 1 : 0.4, cursor: canProceed1 ? 'pointer' : 'not-allowed',
                }}
                disabled={!canProceed1}
                onClick={() => setStep(2)}
              >
                NEXT: ADD FILES <ArrowRightIcon />
              </button>
            </>
          )}

          {/* ── STEP 2: FILES ── */}
          {step === 2 && (
            <>
              <div className="vt323" style={{ fontSize: '2.2rem', marginBottom: '8px', letterSpacing: 3 }}>
                STEP 2 — ADD YOUR FILES
              </div>
              <div className="vt323" style={{ color: '#666', fontSize: '1.1rem', marginBottom: '32px' }}>
                Drag & drop files here, or click Browse. We'll auto-detect secrets!
              </div>

              <div
                ref={dropZoneRef}
                style={{
                  border: `3px dashed ${isDragging ? '#0969DA' : '#999'}`,
                  background: isDragging ? '#EFF6FF' : '#FAFAFA',
                  padding: '60px 32px', textAlign: 'center',
                  cursor: 'pointer', transition: 'all 0.2s',
                  marginBottom: '20px',
                }}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <div style={{ marginBottom: '12px', color: isDragging ? '#0969DA' : '#000' }}>
                  {isDragging ? <DownloadIcon sx={{ fontSize: '4rem' }} /> : <UploadFileIcon sx={{ fontSize: '4rem' }} />}
                </div>
                <div className="vt323" style={{ fontSize: '1.5rem', letterSpacing: 2, marginBottom: '8px' }}>
                  {isDragging ? 'DROP FILES HERE' : 'DRAG & DROP YOUR PROJECT FILES'}
                </div>
                <div className="vt323" style={{ fontSize: '1rem', color: '#666' }}>
                  or click anywhere in this box to browse
                </div>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                multiple
                style={{ display: 'none' }}
                onChange={(e) => e.target.files && addFiles(e.target.files)}
              />

              <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
                <button className="pixel-button primary" onClick={() => fileInputRef.current?.click()} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FileIcon fontSize="small" /> BROWSE FILES
                </button>
                {files.length > 0 && (
                  <button className="pixel-button" style={{ color: '#cf222e', borderColor: '#cf222e', display: 'flex', alignItems: 'center', gap: 8 }} onClick={() => setFiles([])}>
                    <DeleteIcon fontSize="small" /> CLEAR ALL
                  </button>
                )}
              </div>

              {files.length > 0 && (
                <div className="pixel-border" style={{ background: '#fff' }}>
                  <div className="vt323" style={{
                    background: '#000', color: '#fff', padding: '10px 16px',
                    display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem',
                  }}>
                    <span>FILES ADDED ({files.length})</span>
                    <span>
                      <span style={{ color: '#7EE8A2' }}>{safe.length} SAFE</span>
                      {secrets.length > 0 && <> · <span style={{ color: '#FFB3B3' }}>{secrets.length} SECRETS</span></>}
                      {excluded.length > 0 && <> · <span style={{ color: '#FFD97D' }}>{excluded.length} EXCLUDED</span></>}
                    </span>
                  </div>
                  <div style={{ maxHeight: '320px', overflowY: 'auto' }}>
                    {files.map((f) => (
                      <div key={f.id} style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '8px 12px', borderBottom: '1px solid #eee',
                        background: f.sensitivity ? '#fff8f0' : '#fff',
                      }}>
                        <span style={{ display: 'flex', alignItems: 'center' }}>{getFileIcon(f.name)}</span>
                        <span style={{ flex: 1, fontFamily: 'monospace', fontSize: '0.85rem', wordBreak: 'break-all' }}>
                          {f.name}
                        </span>
                        <span className="vt323" style={{ color: '#666', fontSize: '1rem', whiteSpace: 'nowrap' }}>
                          {formatSize(f.size)}
                        </span>
                        {f.sensitivity && (
                          <span className="vt323" style={{
                            display: 'flex', alignItems: 'center', padding: '2px 8px',
                            background: f.sensitivity.color + '20', border: `2px solid ${f.sensitivity.color}`,
                            color: f.sensitivity.color, fontSize: '0.9rem', marginLeft: '8px',
                          }}>
                            {f.sensitivity.label}
                          </span>
                        )}
                        <button
                          style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#999', display: 'flex' }}
                          onClick={() => removeFile(f.id)}
                        ><CloseIcon fontSize="small" /></button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button className="pixel-button" style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }} onClick={() => setStep(1)}>
                  <ArrowLeftIcon /> BACK
                </button>
                <button
                  className="pixel-button primary"
                  style={{
                    flex: 2, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8,
                    opacity: canProceed2 ? 1 : 0.4, cursor: canProceed2 ? 'pointer' : 'not-allowed',
                  }}
                  disabled={!canProceed2}
                  onClick={() => setStep(3)}
                >
                  NEXT: REVIEW PROTECTION <ArrowRightIcon />
                </button>
              </div>
            </>
          )}

          {/* ── STEP 3: REVIEW ── */}
          {step === 3 && (
            <>
              <div className="vt323" style={{ fontSize: '2.2rem', marginBottom: '8px', letterSpacing: 3 }}>
                STEP 3 — REVIEW & PROTECT
              </div>
              <div className="vt323" style={{ color: '#666', fontSize: '1.1rem', marginBottom: '32px' }}>
                Here's what we detected and what we'll protect automatically.
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '12px', marginBottom: '24px' }}>
                {[
                  { label: 'TOTAL FILES', value: files.length, color: '#0969DA' },
                  { label: 'WILL UPLOAD', value: safe.length + secrets.length + keys.length, color: '#2da44e' },
                  { label: 'SECRETS BLOCKED', value: secrets.length + keys.length, color: '#cf222e' },
                  { label: 'FOLDERS EXCLUDED', value: excluded.length, color: '#9a6700' },
                ].map((card) => (
                  <div key={card.label} className="vt323 pixel-border" style={{ borderColor: card.color, padding: '16px', textAlign: 'center', background: '#fff' }}>
                    <div style={{ fontSize: '2rem', color: card.color }}>{card.value}</div>
                    <div style={{ fontSize: '0.9rem', color: '#666', letterSpacing: 1 }}>{card.label}</div>
                  </div>
                ))}
              </div>

              {(secrets.length > 0 || excluded.length > 0 || keys.length > 0) && (
                <div className="vt323 pixel-border" style={{ borderColor: '#cf222e', padding: '24px', background: '#fff', marginBottom: '20px' }}>
                  <div style={{ fontSize: '1.2rem', color: '#cf222e', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <SecurityIcon /> AUTO-PROTECTION ACTIVATED
                  </div>
                  <div style={{ fontSize: '0.95rem', color: '#444', marginBottom: '16px' }}>
                    We found sensitive items. They'll be added to .gitignore automatically so they NEVER reach GitHub.
                  </div>
                  {[...secrets, ...keys].map((f) => {
                    const SIcon = f.sensitivity.icon;
                    return (
                      <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: '1px solid #fee' }}>
                        <SIcon fontSize="small" sx={{ color: '#cf222e' }} />
                        <span style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{f.name}</span>
                        <span className="vt323" style={{
                          padding: '2px 8px', background: '#cf222e20', border: '2px solid #cf222e',
                          color: '#cf222e', fontSize: '0.9rem', marginLeft: 'auto'
                        }}>Will be in .gitignore</span>
                      </div>
                    )
                  })}
                  {excluded.map((f) => {
                    const SIcon = f.sensitivity.icon;
                    return (
                      <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: '1px solid #fef3c7' }}>
                        <SIcon fontSize="small" sx={{ color: '#9a6700' }} />
                        <span style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{f.name}</span>
                        <span className="vt323" style={{
                          padding: '2px 8px', background: '#9a670020', border: '2px solid #9a6700',
                          color: '#9a6700', fontSize: '0.9rem', marginLeft: 'auto'
                        }}>Skipped (excluded folder)</span>
                      </div>
                    )
                  })}
                </div>
              )}

              <div className="pixel-border" style={{ padding: '24px', background: '#fff' }}>
                <label className="vt323" style={{ fontSize: '1.1rem', display: 'block', marginBottom: '8px' }}>
                  COMMIT MESSAGE — What does this version do?
                </label>
                <input
                  className="vt323"
                  style={{
                    width: '100%', border: '3px solid #000', padding: '12px 16px',
                    fontSize: '1.3rem', outline: 'none', background: '#fff'
                  }}
                  placeholder="Initial commit — my awesome project"
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                />
                <div className="vt323" style={{ marginTop: '8px', color: '#666', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <BulbIcon fontSize="small" /> Good examples: "Add login feature", "Fix bug in checkout", "Initial version"
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                <button className="pixel-button" style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }} onClick={() => setStep(2)}>
                  <ArrowLeftIcon /> BACK
                </button>
                <button className="pixel-button primary" style={{ flex: 2, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }} onClick={() => setStep(4)}>
                  NEXT: LAUNCH TO GITHUB <RocketIcon />
                </button>
              </div>
            </>
          )}

          {/* ── STEP 4: PUSH ── */}
          {step === 4 && (
            <>
              <div className="vt323" style={{ fontSize: '2.2rem', marginBottom: '8px', letterSpacing: 3, display: 'flex', alignItems: 'center', gap: 8 }}>
                STEP 4 — LAUNCH TO GITHUB <RocketIcon fontSize="large" />
              </div>
              <div className="vt323" style={{ color: '#666', fontSize: '1.1rem', marginBottom: '32px' }}>
                Everything is ready. One click and your code goes live!
              </div>

              {pushStatus === 'idle' && (
                <div className="vt323 pixel-border" style={{ padding: '24px', background: '#fff', marginBottom: '24px' }}>
                  <div style={{ fontSize: '1.2rem', marginBottom: '16px' }}>LAUNCH CHECKLIST</div>
                  {[
                    { done: true, label: `Repository name: ${nameStatus?.sanitized_name}` },
                    { done: true, label: `Visibility: ${isPrivate ? 'Private' : 'Public'}` },
                    { done: true, label: `Files to upload: ${files.filter(f => f.sensitivity?.type !== 'excluded').length}` },
                    { done: true, label: `Secrets protected: ${secrets.length + keys.length} file(s)` },
                    { done: true, label: `.gitignore: Auto-generated` },
                    { done: !!commitMessage, label: `Commit message: "${commitMessage || '(not set — will use default)'}"` },
                  ].map((item, i) => (
                    <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid #eee', display: 'flex', alignItems: 'center', gap: '12px' }}>
                      {item.done ? <CheckIcon sx={{ color: '#2da44e' }} /> : <InfoIcon sx={{ color: '#9a6700' }} />}
                      <span style={{ fontSize: '1.1rem' }}>{item.label}</span>
                    </div>
                  ))}
                </div>
              )}

              {pushLog.length > 0 && (
                <div className="pixel-border" style={{ background: '#0d1117', padding: '20px', marginBottom: '24px' }}>
                  <div className="vt323" style={{ color: '#7ee787', fontSize: '1rem', marginBottom: '12px', letterSpacing: 2 }}>
                    LIVE PUSH LOG
                  </div>
                  {pushLog.map((line, i) => (
                    <span key={i} style={{
                      display: 'block', padding: '6px 0',
                      fontFamily: 'monospace', fontSize: '0.9rem',
                      borderBottom: '1px solid #eee',
                      color: i === pushLog.length - 1 ? '#fff' : '#8b949e'
                    }}>
                      $ {line}
                    </span>
                  ))}
                  {pushStatus === 'pushing' && (
                    <span className="vt323" style={{ color: '#f0883e', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8, marginTop: '8px' }}>
                      <HourglassIcon fontSize="small" /> Working...
                    </span>
                  )}
                </div>
              )}

              {pushStatus === 'done' && pushResult && (
                <div className="pixel-border" style={{ padding: '32px', textAlign: 'center', background: '#DCFCE7', borderColor: '#2da44e' }}>
                  <PartyIcon sx={{ fontSize: '4rem', color: '#1a7f37', mb: 2 }} />
                  <div className="vt323" style={{ fontSize: '2rem', color: '#1a7f37', marginBottom: '8px', letterSpacing: 3 }}>
                    SUCCESSFULLY LAUNCHED!
                  </div>
                  <div className="vt323" style={{ fontSize: '1.1rem', color: '#444', marginBottom: '24px' }}>
                    {pushResult.files_pushed} file(s) pushed · .gitignore created · {pushResult.detected_sensitive?.length || 0} secret(s) protected
                  </div>
                  <a href={pushResult.repo_url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                    <button className="pixel-button" style={{ background: '#2da44e', color: '#fff', borderColor: '#2da44e', display: 'flex', alignItems: 'center', gap: 8, margin: '0 auto' }}>
                      <LinkIcon /> VIEW ON GITHUB
                    </button>
                  </a>
                  <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'center', gap: 12 }}>
                    <button
                      className="pixel-button primary"
                      style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                      onClick={() => navigate(`/dashboard/${nameStatus?.username}/${nameStatus?.sanitized_name}`)}
                    >
                      <SecurityIcon /> SECURITY AUDIT
                    </button>
                    <button className="pixel-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }} onClick={() => {
                      setStep(1); setRepoName(''); setFiles([]); setPushStatus('idle');
                      setPushResult(null); setPushLog([]); setCommitMessage('');
                    }}>
                      <AddIcon /> CREATE ANOTHER
                    </button>
                  </div>
                </div>
              )}

              {pushStatus === 'error' && (
                <div className="pixel-border" style={{ padding: '24px', background: '#FEE2E2', borderColor: '#cf222e', marginBottom: '20px' }}>
                  <div className="vt323" style={{ fontSize: '1.3rem', color: '#cf222e', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <ErrorIcon /> PUSH FAILED
                  </div>
                  <div style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{pushError}</div>
                </div>
              )}

              {pushStatus === 'idle' && (
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button className="pixel-button" style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }} onClick={() => setStep(3)}>
                    <ArrowLeftIcon /> BACK
                  </button>
                  <button className="pixel-button" style={{ flex: 2, background: '#2da44e', borderColor: '#2da44e', color: '#fff', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }} onClick={handlePush}>
                    LAUNCH TO GITHUB NOW <RocketIcon />
                  </button>
                </div>
              )}

              {pushStatus === 'error' && (
                <button className="pixel-button" style={{ width: '100%', borderColor: '#cf222e', color: '#cf222e', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }} onClick={() => { setPushStatus('idle'); setPushLog([]); }}>
                  <RefreshIcon /> TRY AGAIN
                </button>
              )}
            </>
          )}
        </div>

        {/* Sidebar */}
        <div style={{ padding: '32px 28px', background: '#F8F8F8' }}>
          <div className="pixel-border" style={{ padding: '20px', background: '#EFF6FF', borderColor: '#0969DA', marginBottom: '24px' }}>
            {(() => {
              const SIcon = EXPLANATIONS[step]?.icon;
              return <SIcon sx={{ fontSize: '3rem', color: '#0969DA', mb: 1 }} />;
            })()}
            <div className="vt323" style={{ fontSize: '1.2rem', letterSpacing: 2, marginBottom: '12px', color: '#0969DA' }}>
              {EXPLANATIONS[step]?.what}
            </div>
            <div className="vt323" style={{ fontSize: '1.1rem', lineHeight: 1.4, color: '#333' }}>
              {EXPLANATIONS[step]?.body}
            </div>
          </div>

          {/* Step progress */}
          <div className="pixel-border" style={{ padding: '20px', background: '#fff' }}>
            <div className="vt323" style={{ fontSize: '1.1rem', letterSpacing: 2, marginBottom: '16px' }}>YOUR PROGRESS</div>
            {STEPS.map((s) => (
              <div key={s.id} style={{
                display: 'flex', gap: '12px', alignItems: 'center',
                padding: '10px 0', borderBottom: '1px solid #eee',
                opacity: step >= s.id ? 1 : 0.35,
              }}>
                <span className="vt323" style={{
                  width: '32px', height: '32px', border: '2px solid #000',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1rem',
                  background: step > s.id ? '#2da44e' : step === s.id ? '#0969DA' : '#fff',
                  color: step >= s.id ? '#fff' : '#000',
                }}>
                  {step > s.id ? <CheckIcon fontSize="small" /> : s.id}
                </span>
                <div>
                  <div className="vt323" style={{ fontSize: '1rem', letterSpacing: 1 }}>{s.title}</div>
                  <div className="vt323" style={{ fontSize: '0.85rem', color: '#666' }}>
                    {step > s.id ? 'COMPLETED' : step === s.id ? 'IN PROGRESS...' : 'PENDING'}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {(nameStatus?.available || files.length > 0) && (
            <div className="pixel-border" style={{ padding: '20px', marginTop: '16px', background: '#fff' }}>
              <div className="vt323" style={{ fontSize: '1rem', letterSpacing: 2, marginBottom: '12px' }}>REPO PREVIEW</div>
              {nameStatus?.available && (
                <div className="vt323" style={{ fontSize: '1.1rem', marginBottom: '6px' }}>
                  <span style={{ opacity: 0.6 }}>github.com/</span>
                  <strong>{nameStatus.username}/{nameStatus.sanitized_name}</strong>
                </div>
              )}
              {files.length > 0 && (
                <div className="vt323" style={{ fontSize: '1rem', color: '#666', marginTop: '8px', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <FileIcon fontSize="small" /> {files.length} file(s) · {formatSize(files.reduce((a, f) => a + f.size, 0))}
                </div>
              )}
              {isPrivate !== undefined && nameStatus?.available && (
                <div className="vt323" style={{ fontSize: '1rem', marginTop: '8px', display: 'flex', alignItems: 'center', gap: 4 }}>
                  {isPrivate ? <LockIcon fontSize="small" /> : <InfoIcon fontSize="small" />} {isPrivate ? 'Private' : 'Public'}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
