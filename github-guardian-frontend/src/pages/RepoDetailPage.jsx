import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { client } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  GitHub as GitHubIcon,
  ArrowBack as ArrowLeftIcon,
  AccountTree as BranchIcon,
  RocketLaunch as PushIcon,
  UploadFile as UploadIcon,
  Close as CloseIcon,
  Check as CheckIcon,
  InsertDriveFile as FileIcon,
  HourglassEmpty as HourglassIcon,
  ErrorOutline as ErrorIcon,
  Celebration as PartyIcon,
  Link as LinkIcon,
  Lock as LockIcon,
  Public as PublicIcon,
  Add as AddIcon,
  MergeType as MergeIcon,
  AutoFixHigh as AIIcon,
  Warning as WarningIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
} from '@mui/icons-material';

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};

// Step IDs
const STEPS = {
  BRANCHES: 'branches',   // Step 1: View branches + create new one
  FILES: 'files',          // Step 2: Upload files to the new branch
  MERGE: 'merge',          // Step 3: Pick target branch to merge into
  RESULT: 'result',        // Step 4: Show merge result
};

export default function RepoDetailPage() {
  const { repoName } = useParams();
  const navigate = useNavigate();
  const { user, loading } = useAuth();
  const fileInputRef = useRef(null);
  const dropRef = useRef(null);

  // Repo info
  const [repoData, setRepoData] = useState(null);
  const [repoLoading, setRepoLoading] = useState(true);
  const [repoError, setRepoError] = useState('');

  // Wizard state
  const [step, setStep] = useState(STEPS.BRANCHES);

  // Step 1: Create branch
  const [newBranchName, setNewBranchName] = useState('');
  const [baseBranch, setBaseBranch] = useState('');
  const [creatingBranch, setCreatingBranch] = useState(false);
  const [createdBranch, setCreatedBranch] = useState(null); // name of branch after creation
  const [branchError, setBranchError] = useState('');

  // Step 2: Files
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [commitMessage, setCommitMessage] = useState('');
  const [pushingFiles, setPushingFiles] = useState(false);
  const [filesPushed, setFilesPushed] = useState(false);
  const [filesError, setFilesError] = useState('');

  // Step 3: Merge
  const [targetBranch, setTargetBranch] = useState('');
  const [merging, setMerging] = useState(false);
  const [mergeLog, setMergeLog] = useState([]);

  // Step 4: Result
  const [mergeResult, setMergeResult] = useState(null);

  // Load repo data
  useEffect(() => {
    if (!user) return;
    setRepoLoading(true);
    client.get(`/desktop/branches/${encodeURIComponent(repoName)}`)
      .then(res => {
        setRepoData(res.data);
        setBaseBranch(res.data.default_branch);
        setTargetBranch(res.data.default_branch);
      })
      .catch(err => setRepoError(err.response?.data?.detail || 'Failed to load repository'))
      .finally(() => setRepoLoading(false));
  }, [repoName, user]);

  // ── File Handling ─────────────────────────────────────────────────────────
  const addFiles = useCallback((newFiles) => {
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name));
      const toAdd = Array.from(newFiles)
        .filter(f => !existing.has(f.webkitRelativePath || f.name))
        .map(f => ({
          id: `${f.name}-${f.size}-${Date.now()}`,
          name: f.webkitRelativePath || f.name,
          size: f.size,
          fileObj: f,
        }));
      return [...prev, ...toAdd];
    });
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault(); setIsDragging(false);
    if (e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files);
  }, [addFiles]);

  // ── Step 1: Create Branch ─────────────────────────────────────────────────
  const handleCreateBranch = async () => {
    if (!newBranchName.trim()) return;
    setCreatingBranch(true);
    setBranchError('');
    try {
      const form = new FormData();
      form.append('repo_name', repoName);
      form.append('new_branch_name', newBranchName.trim());
      form.append('base_branch', baseBranch);
      const { data } = await client.post('/desktop/create-branch', form);
      setCreatedBranch(data.branch_name);
      setCommitMessage(`Add files to ${data.branch_name}`);
      setStep(STEPS.FILES);
    } catch (e) {
      setBranchError(e.response?.data?.detail || 'Failed to create branch');
    } finally {
      setCreatingBranch(false);
    }
  };

  // ── Step 2: Push Files to Branch ──────────────────────────────────────────
  const handlePushFiles = async () => {
    if (!files.length || !createdBranch) return;
    setPushingFiles(true);
    setFilesError('');
    try {
      const form = new FormData();
      form.append('repo_name', repoName);
      form.append('branch_name', createdBranch);
      form.append('commit_message', commitMessage || `Add files to ${createdBranch}`);
      for (const f of files) form.append('files', f.fileObj, f.name);

      await client.post('/desktop/push-to-branch', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });
      setFilesPushed(true);
      setStep(STEPS.MERGE);
    } catch (e) {
      setFilesError(e.response?.data?.detail || 'Failed to push files');
    } finally {
      setPushingFiles(false);
    }
  };

  // ── Step 3: Merge Branch ──────────────────────────────────────────────────
  const handleMerge = async () => {
    if (!createdBranch || !targetBranch) return;
    setMerging(true);
    setMergeLog([]);

    const log = (msg) => setMergeLog(prev => [...prev, msg]);

    log(`Comparing "${createdBranch}" with "${targetBranch}"...`);
    await new Promise(r => setTimeout(r, 500));
    log('Scanning for file conflicts...');
    await new Promise(r => setTimeout(r, 600));

    try {
      const form = new FormData();
      form.append('repo_name', repoName);
      form.append('source_branch', createdBranch);
      form.append('target_branch', targetBranch);

      const { data } = await client.post('/desktop/merge-branch', form, { timeout: 180000 });

      if (data.conflict_results?.total_conflicts > 0) {
        log(`Found ${data.conflict_results.total_conflicts} conflict(s).`);
        if (data.conflict_results.ai_fixed?.length > 0)
          log(`AI successfully fixed ${data.conflict_results.ai_fixed.length} conflict(s).`);
      } else {
        log('No conflicts found — clean merge!');
      }

      if (data.merged) log(`Merged into "${targetBranch}" successfully!`);

      setMergeResult(data);
      setStep(STEPS.RESULT);
    } catch (e) {
      log(`Merge failed: ${e.response?.data?.detail || e.message}`);
      setMergeResult({ success: false, merged: false, message: e.response?.data?.detail || e.message });
      setStep(STEPS.RESULT);
    } finally {
      setMerging(false);
    }
  };

  if (loading || repoLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'VT323', monospace", fontSize: '1.5rem' }}>
        <HourglassIcon sx={{ mr: 1 }} /> Loading repository...
      </div>
    );
  }

  if (repoError) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, padding: 32 }}>
        <ErrorIcon sx={{ fontSize: '4rem', color: '#cf222e' }} />
        <div className="vt323" style={{ fontSize: '1.5rem' }}>{repoError}</div>
        <button className="pixel-button" onClick={() => navigate('/history')}>BACK TO REPOS</button>
      </div>
    );
  }

  const stepList = [
    { key: STEPS.BRANCHES, label: 'BRANCH', num: 1 },
    { key: STEPS.FILES, label: 'FILES', num: 2 },
    { key: STEPS.MERGE, label: 'MERGE', num: 3 },
    { key: STEPS.RESULT, label: 'DONE', num: 4 },
  ];
  const currentStepIdx = stepList.findIndex(s => s.key === step);

  return (
    <div style={{ minHeight: '100vh', background: '#F8F8F8' }}>

      {/* Header */}
      <div style={{ background: '#000', color: '#fff', padding: '16px 32px', display: 'flex', alignItems: 'center', gap: 16, borderBottom: '4px solid #0969DA' }}>
        <GitHubIcon sx={{ fontSize: '2.5rem' }} />
        <div>
          <div className="vt323" style={{ fontSize: '1.8rem', letterSpacing: 4 }}>{repoName}</div>
          <div className="vt323" style={{ fontSize: '1rem', opacity: 0.7, letterSpacing: 2 }}>
            BRANCH · UPLOAD · MERGE — STEP BY STEP
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          {repoData && (
            <span className="vt323" style={{ color: repoData.private ? '#cf222e' : '#2da44e', border: `2px solid ${repoData.private ? '#cf222e' : '#2da44e'}`, padding: '4px 12px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 6 }}>
              {repoData.private ? <><LockIcon fontSize="small" /> PRIVATE</> : <><PublicIcon fontSize="small" /> PUBLIC</>}
            </span>
          )}
          <a href={repoData?.html_url} target="_blank" rel="noreferrer">
            <button className="pixel-button" style={{ background: 'transparent', color: '#fff', borderColor: '#fff' }}><LinkIcon fontSize="small" sx={{ mr: 0.5 }} /> GITHUB</button>
          </a>
          <button className="pixel-button" style={{ background: 'transparent', color: '#fff', borderColor: '#fff' }} onClick={() => navigate('/history')}>
            <ArrowLeftIcon fontSize="small" /> BACK
          </button>
        </div>
      </div>

      {/* Step Progress Bar */}
      <div style={{ display: 'flex', borderBottom: '3px solid #000', background: '#fff' }}>
        {stepList.map((s, i) => {
          const isDone = i < currentStepIdx;
          const isActive = s.key === step;
          return (
            <div key={s.key} className="vt323" style={{
              flex: 1, padding: '14px', borderRight: '2px solid #000',
              background: isDone ? '#2da44e' : isActive ? '#0969DA' : '#F8F8F8',
              color: isDone || isActive ? '#fff' : '#888',
              fontSize: '1.1rem', letterSpacing: 2,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            }}>
              {isDone ? <CheckIcon fontSize="small" /> : null} {s.num}. {s.label}
            </div>
          );
        })}
      </div>

      <div style={{ maxWidth: 860, margin: '0 auto', padding: '40px 32px' }}>

        {/* ── STEP 1: VIEW BRANCHES & CREATE NEW ── */}
        {step === STEPS.BRANCHES && (
          <>
            <div className="vt323" style={{ fontSize: '2rem', letterSpacing: 3, marginBottom: 8 }}>STEP 1 — CREATE A NEW BRANCH</div>
            <div className="vt323" style={{ color: '#666', fontSize: '1.1rem', marginBottom: 28 }}>
              Existing branches are shown below. Give your new branch a name, pick which branch to base it on, and we'll create it instantly.
            </div>

            {/* Existing Branches */}
            <div className="pixel-border" style={{ background: '#fff', marginBottom: 28 }}>
              <div className="vt323" style={{ background: '#000', color: '#aaa', padding: '10px 16px', fontSize: '1rem', letterSpacing: 2, display: 'flex', alignItems: 'center', gap: 8 }}>
                <BranchIcon fontSize="small" /> CURRENT BRANCHES ({repoData?.branches?.length})
              </div>
              {repoData?.branches?.map(b => (
                <div key={b.name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', borderBottom: '1px solid #eee' }}>
                  <BranchIcon sx={{ fontSize: 16, color: '#0969DA' }} />
                  <span className="vt323" style={{ fontSize: '1.2rem', flex: 1 }}>{b.name}</span>
                  {b.is_default && <span className="vt323" style={{ fontSize: '0.8rem', color: '#2da44e', border: '1px solid #2da44e', padding: '1px 6px' }}>DEFAULT</span>}
                  <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#888', maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {b.last_commit_message}
                  </span>
                </div>
              ))}
            </div>

            {/* Create New Branch Form */}
            <div className="pixel-border" style={{ background: '#fff', padding: '24px', marginBottom: 24 }}>
              <div className="vt323" style={{ fontSize: '1.3rem', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <AddIcon /> CREATE NEW BRANCH
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div>
                  <label className="vt323" style={{ fontSize: '1rem', display: 'block', marginBottom: 6 }}>NEW BRANCH NAME <span style={{ color: '#cf222e' }}>*</span></label>
                  <input
                    className="vt323"
                    style={{ width: '100%', border: '3px solid #000', padding: '10px 14px', fontSize: '1.2rem', outline: 'none' }}
                    placeholder="feature/my-new-feature"
                    value={newBranchName}
                    onChange={e => { setNewBranchName(e.target.value); setBranchError(''); }}
                    onKeyDown={e => e.key === 'Enter' && handleCreateBranch()}
                  />
                </div>
                <div>
                  <label className="vt323" style={{ fontSize: '1rem', display: 'block', marginBottom: 6 }}>BASE BRANCH (copy from)</label>
                  <select
                    className="vt323"
                    style={{ width: '100%', border: '3px solid #000', padding: '10px 14px', fontSize: '1.2rem', outline: 'none', background: '#fff' }}
                    value={baseBranch}
                    onChange={e => setBaseBranch(e.target.value)}
                  >
                    {repoData?.branches?.map(b => <option key={b.name} value={b.name}>{b.name} {b.is_default ? '(default)' : ''}</option>)}
                  </select>
                </div>
              </div>

              {branchError && (
                <div className="vt323" style={{ color: '#cf222e', fontSize: '1rem', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <ErrorIcon fontSize="small" /> {branchError}
                </div>
              )}

              <button
                className="pixel-button primary"
                style={{ width: '100%', fontSize: '1.2rem', padding: '12px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8,
                  opacity: newBranchName.trim() && !creatingBranch ? 1 : 0.5, cursor: newBranchName.trim() && !creatingBranch ? 'pointer' : 'not-allowed' }}
                disabled={!newBranchName.trim() || creatingBranch}
                onClick={handleCreateBranch}
              >
                {creatingBranch ? <><HourglassIcon /> CREATING...</> : <><AddIcon /> CREATE BRANCH & CONTINUE</>}
              </button>
            </div>
          </>
        )}

        {/* ── STEP 2: UPLOAD FILES ── */}
        {step === STEPS.FILES && (
          <>
            <div className="vt323" style={{ fontSize: '2rem', letterSpacing: 3, marginBottom: 8 }}>
              STEP 2 — ADD FILES TO <span style={{ color: '#0969DA' }}>{createdBranch}</span>
            </div>
            <div className="vt323" style={{ color: '#666', fontSize: '1.1rem', marginBottom: 28 }}>
              Upload the files you want to push to this new branch.
            </div>

            <div
              ref={dropRef}
              onDrop={onDrop}
              onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `3px dashed ${isDragging ? '#0969DA' : '#ccc'}`, background: isDragging ? '#EFF6FF' : '#FAFAFA',
                padding: '48px 32px', textAlign: 'center', cursor: 'pointer', marginBottom: 20, transition: 'all 0.2s',
              }}
            >
              <UploadIcon sx={{ fontSize: '3.5rem', color: isDragging ? '#0969DA' : '#aaa', mb: 1 }} />
              <div className="vt323" style={{ fontSize: '1.4rem', color: isDragging ? '#0969DA' : '#666' }}>
                {isDragging ? 'DROP FILES HERE' : 'DRAG & DROP FILES'}
              </div>
              <div className="vt323" style={{ fontSize: '1rem', color: '#aaa', marginTop: 4 }}>or click to browse</div>
            </div>
            <input ref={fileInputRef} type="file" multiple style={{ display: 'none' }}
              onChange={e => e.target.files && addFiles(e.target.files)} />

            {files.length > 0 && (
              <div className="pixel-border" style={{ background: '#fff', marginBottom: 20 }}>
                <div className="vt323" style={{ background: '#000', color: '#7ee787', padding: '8px 16px', fontSize: '1rem' }}>
                  {files.length} FILE(S) READY
                </div>
                {files.map(f => (
                  <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', borderBottom: '1px solid #eee' }}>
                    <FileIcon fontSize="small" sx={{ color: '#666' }} />
                    <span style={{ flex: 1, fontFamily: 'monospace', fontSize: '0.85rem' }}>{f.name}</span>
                    <span style={{ color: '#888', fontFamily: 'monospace', fontSize: '0.8rem' }}>{formatSize(f.size)}</span>
                    <button style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#999' }}
                      onClick={() => setFiles(prev => prev.filter(x => x.id !== f.id))}>
                      <CloseIcon fontSize="small" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="pixel-border" style={{ padding: '20px', background: '#fff', marginBottom: 20 }}>
              <label className="vt323" style={{ fontSize: '1rem', display: 'block', marginBottom: 8 }}>COMMIT MESSAGE</label>
              <input
                className="vt323"
                style={{ width: '100%', border: '3px solid #000', padding: '10px 14px', fontSize: '1.2rem', outline: 'none' }}
                placeholder={`Add files to ${createdBranch}`}
                value={commitMessage}
                onChange={e => setCommitMessage(e.target.value)}
              />
            </div>

            {filesError && (
              <div className="vt323" style={{ color: '#cf222e', fontSize: '1rem', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                <ErrorIcon fontSize="small" /> {filesError}
              </div>
            )}

            <button
              className="pixel-button"
              style={{
                width: '100%', background: files.length > 0 && !pushingFiles ? '#0969DA' : '#ccc',
                borderColor: files.length > 0 && !pushingFiles ? '#0969DA' : '#ccc',
                color: '#fff', fontSize: '1.3rem', padding: '14px',
                display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10,
                cursor: files.length > 0 && !pushingFiles ? 'pointer' : 'not-allowed',
              }}
              disabled={files.length === 0 || pushingFiles}
              onClick={handlePushFiles}
            >
              {pushingFiles ? <><HourglassIcon /> PUSHING FILES...</> : <><PushIcon /> PUSH FILES TO BRANCH</>}
            </button>
          </>
        )}

        {/* ── STEP 3: PICK MERGE TARGET ── */}
        {step === STEPS.MERGE && (
          <>
            <div className="vt323" style={{ fontSize: '2rem', letterSpacing: 3, marginBottom: 8 }}>STEP 3 — MERGE INTO WHICH BRANCH?</div>
            <div className="vt323" style={{ color: '#666', fontSize: '1.1rem', marginBottom: 28 }}>
              Files pushed to <strong>{createdBranch}</strong> successfully! Now choose which branch to merge it into.
              We'll check for conflicts first — if any exist, AI will attempt to fix them automatically.
            </div>

            <div className="pixel-border" style={{ background: '#EFF6FF', borderColor: '#0969DA', padding: '20px', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
              <BranchIcon sx={{ fontSize: '2.5rem', color: '#0969DA' }} />
              <div>
                <div className="vt323" style={{ fontSize: '1.2rem', color: '#0969DA' }}>MERGING: <strong>{createdBranch}</strong></div>
                <div className="vt323" style={{ fontSize: '1rem', color: '#555' }}>Files will be merged into your chosen target branch below</div>
              </div>
            </div>

            <div className="pixel-border" style={{ padding: '24px', background: '#fff', marginBottom: 24 }}>
              <label className="vt323" style={{ fontSize: '1.1rem', display: 'block', marginBottom: 10 }}>MERGE INTO (TARGET BRANCH)</label>
              <select
                className="vt323"
                style={{ width: '100%', border: '3px solid #000', padding: '12px 16px', fontSize: '1.3rem', outline: 'none', background: '#fff' }}
                value={targetBranch}
                onChange={e => setTargetBranch(e.target.value)}
              >
                {repoData?.branches?.filter(b => b.name !== createdBranch).map(b => (
                  <option key={b.name} value={b.name}>{b.name} {b.is_default ? '(default / main)' : ''}</option>
                ))}
              </select>
            </div>

            {/* Merge Log */}
            {mergeLog.length > 0 && (
              <div className="pixel-border" style={{ background: '#0d1117', padding: '20px', marginBottom: 20 }}>
                <div className="vt323" style={{ color: '#7ee787', fontSize: '1rem', marginBottom: 12, letterSpacing: 2 }}>LIVE MERGE LOG</div>
                {mergeLog.map((line, i) => (
                  <div key={i} style={{ padding: '5px 0', fontFamily: 'monospace', fontSize: '0.9rem', color: i === mergeLog.length - 1 ? '#fff' : '#8b949e', borderBottom: '1px solid #30363d' }}>
                    $ {line}
                  </div>
                ))}
                {merging && (
                  <div className="vt323" style={{ color: '#f0883e', marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <HourglassIcon fontSize="small" /> Please wait...
                  </div>
                )}
              </div>
            )}

            <button
              className="pixel-button"
              style={{
                width: '100%', background: !merging ? '#8250df' : '#ccc',
                borderColor: !merging ? '#8250df' : '#ccc',
                color: '#fff', fontSize: '1.3rem', padding: '14px',
                display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10,
                cursor: !merging ? 'pointer' : 'not-allowed',
              }}
              disabled={merging}
              onClick={handleMerge}
            >
              {merging
                ? <><HourglassIcon /> CHECKING &amp; MERGING...</>
                : <><MergeIcon /> CHECK CONFLICTS &amp; MERGE INTO {targetBranch.toUpperCase()}</>}
            </button>
          </>
        )}

        {/* ── STEP 4: RESULT ── */}
        {step === STEPS.RESULT && mergeResult && (
          <>
            {/* SUCCESS */}
            {mergeResult.merged && (
              <div className="pixel-border" style={{ padding: '40px', textAlign: 'center', background: '#DCFCE7', borderColor: '#2da44e' }}>
                <PartyIcon sx={{ fontSize: '4rem', color: '#1a7f37', mb: 2 }} />
                <div className="vt323" style={{ fontSize: '2.5rem', color: '#1a7f37', marginBottom: 8, letterSpacing: 3 }}>MERGED SUCCESSFULLY!</div>
                <div className="vt323" style={{ fontSize: '1.2rem', color: '#444', marginBottom: 8 }}>
                  Branch <strong>{mergeResult.source_branch}</strong> merged into <strong>{mergeResult.target_branch}</strong>
                </div>
                {mergeResult.conflict_results?.ai_fixed?.length > 0 && (
                  <div className="vt323" style={{ fontSize: '1.1rem', color: '#2da44e', marginBottom: 20, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 6 }}>
                    <AIIcon fontSize="small" /> AI auto-fixed {mergeResult.conflict_results.ai_fixed.length} conflict(s)
                  </div>
                )}
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24 }}>
                  <a href={mergeResult.pr_url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                    <button className="pixel-button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <LinkIcon /> VIEW PR ON GITHUB
                    </button>
                  </a>
                  <button className="pixel-button primary" onClick={() => navigate('/history')} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <BranchIcon /> BACK TO REPOS
                  </button>
                </div>
              </div>
            )}

            {/* CONFLICT UNFIXABLE */}
            {!mergeResult.merged && mergeResult.reason === 'conflict_unfixable' && (
              <div className="pixel-border" style={{ padding: '40px', textAlign: 'center', background: '#FEF9C3', borderColor: '#9a6700' }}>
                <WarningIcon sx={{ fontSize: '4rem', color: '#9a6700', mb: 2 }} />
                <div className="vt323" style={{ fontSize: '2rem', color: '#9a6700', marginBottom: 12, letterSpacing: 2 }}>SORRY, WE COULDN'T FIX THIS</div>
                <div className="vt323" style={{ fontSize: '1.1rem', color: '#555', maxWidth: 600, margin: '0 auto 20px' }}>
                  {mergeResult.message}
                </div>
                {mergeResult.conflict_results?.ai_failed?.length > 0 && (
                  <div style={{ background: '#fff', border: '2px solid #9a6700', padding: '12px 20px', marginBottom: 20, textAlign: 'left', maxWidth: 500, margin: '0 auto 20px' }}>
                    <div className="vt323" style={{ color: '#9a6700', marginBottom: 8 }}>UNRESOLVABLE FILES:</div>
                    {mergeResult.conflict_results.ai_failed.map(f => (
                      <div key={f} style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#555', padding: '4px 0' }}>• {f}</div>
                    ))}
                  </div>
                )}
                <button className="pixel-button" onClick={() => navigate('/history')} style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '0 auto' }}>
                  <ArrowLeftIcon /> BACK TO REPOS
                </button>
              </div>
            )}

            {/* OTHER FAILURE */}
            {!mergeResult.merged && mergeResult.reason !== 'conflict_unfixable' && (
              <div className="pixel-border" style={{ padding: '40px', textAlign: 'center', background: '#FEE2E2', borderColor: '#cf222e' }}>
                <ErrorIcon sx={{ fontSize: '4rem', color: '#cf222e', mb: 2 }} />
                <div className="vt323" style={{ fontSize: '2rem', color: '#cf222e', marginBottom: 12 }}>MERGE FAILED</div>
                <div style={{ fontFamily: 'monospace', fontSize: '0.9rem', color: '#555' }}>{mergeResult.message}</div>
                <button className="pixel-button" style={{ marginTop: 24, borderColor: '#cf222e', color: '#cf222e' }}
                  onClick={() => { setStep(STEPS.MERGE); setMergeLog([]); }}>
                  TRY AGAIN
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
