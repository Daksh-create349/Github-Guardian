import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  History as HistoryIcon,
  GitHub as GitHubIcon,
  ArrowBack as ArrowLeftIcon,
  AccessTime as TimeIcon,
  MergeType as MergeIcon,
  RocketLaunch as PushIcon,
  ErrorOutline as ErrorIcon,
  Link as LinkIcon,
  Lock as LockIcon,
  Public as PublicIcon,
  Star as StarIcon,
  ForkRight as ForkIcon,
  BugReport as IssueIcon,
  Code as CodeIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { API_AUTH_LOGIN_URL } from '../api/config';

const LANG_COLORS = {
  JavaScript: '#f7df1e', TypeScript: '#3178c6', Python: '#3572A5',
  Go: '#00ADD8', Rust: '#dea584', Java: '#b07219', CSS: '#563d7c',
  HTML: '#e34c26', Ruby: '#701516', Swift: '#ffac45', Kotlin: '#A97BFF',
  Unknown: '#888',
};

export default function PushHistoryPage() {
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  const [repos, setRepos] = useState([]);
  const [guardianLogs, setGuardianLogs] = useState([]);
  const [reposLoading, setReposLoading] = useState(true);
  const [logsLoading, setLogsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('repos'); // 'repos' | 'logs'

  const fetchData = () => {
    if (!user) return;

    // Fetch real GitHub repos
    setReposLoading(true);
    client.get('/desktop/github-repos')
      .then(res => setRepos(res.data))
      .catch(err => console.error('repos error:', err))
      .finally(() => setReposLoading(false));

    // Fetch Guardian push logs
    setLogsLoading(true);
    client.get('/desktop/history')
      .then(res => setGuardianLogs(res.data))
      .catch(err => console.error('logs error:', err))
      .finally(() => setLogsLoading(false));
  };

  useEffect(() => { fetchData(); }, [user]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'VT323', monospace", fontSize: '1.5rem' }}>
        Loading...
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#fff', gap: 20, padding: 32, textAlign: 'center' }}>
        <HistoryIcon sx={{ fontSize: '4rem' }} />
        <div className="vt323" style={{ fontSize: '2.5rem', letterSpacing: 4 }}>SIGN IN REQUIRED</div>
        <button className="pixel-button primary" onClick={() => { window.location.href = API_AUTH_LOGIN_URL; }}>
          SIGN IN WITH GITHUB
        </button>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F8F8F8' }}>
      {/* Header */}
      <div style={{
        background: '#000', color: '#fff', padding: '16px 32px',
        display: 'flex', alignItems: 'center', gap: 16,
        borderBottom: '4px solid #0969DA',
      }}>
        <HistoryIcon sx={{ fontSize: '2.5rem' }} />
        <div>
          <div className="vt323" style={{ fontSize: '1.8rem', letterSpacing: 4 }}>REPOSITORY HUB</div>
          <div className="vt323" style={{ fontSize: '1rem', opacity: 0.7, letterSpacing: 2 }}>
            YOUR GITHUB REPOS &amp; GUARDIAN PUSH LOGS
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="pixel-border" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: '#000', borderColor: '#ffffff50', color: '#fff', boxShadow: 'none' }}>
            <img src={user.avatar_url} alt={user.username} style={{ width: 28, height: 28, borderRadius: '50%' }} />
            <span className="vt323" style={{ fontSize: '1rem', opacity: 0.9 }}>@{user.username}</span>
          </div>
          <button
            className="pixel-button"
            style={{ background: 'transparent', color: '#fff', borderColor: '#fff', display: 'flex', alignItems: 'center', gap: 6 }}
            onClick={fetchData}
          >
            <RefreshIcon fontSize="small" /> REFRESH
          </button>
          <button className="pixel-button" style={{ background: 'transparent', color: '#fff', borderColor: '#fff' }} onClick={() => navigate('/desktop')}>
            <ArrowLeftIcon sx={{ mr: 0.5 }} fontSize="small" /> BACK
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '3px solid #000', background: '#fff' }}>
        {[
          { key: 'repos', label: `YOUR REPOS (${repos.length})`, icon: GitHubIcon },
          { key: 'logs', label: `GUARDIAN LOGS (${guardianLogs.length})`, icon: PushIcon },
        ].map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              className="vt323"
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '14px 32px', border: 'none', borderRight: '2px solid #000',
                background: activeTab === tab.key ? '#0969DA' : '#fff',
                color: activeTab === tab.key ? '#fff' : '#666',
                fontSize: '1.1rem', letterSpacing: 2, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
                borderBottom: activeTab === tab.key ? '3px solid #0969DA' : 'none',
                transition: 'all 0.2s',
              }}
            >
              <Icon fontSize="small" /> {tab.label}
            </button>
          );
        })}
      </div>

      <div style={{ padding: '32px 48px', maxWidth: 1100, margin: '0 auto' }}>

        {/* ── GitHub Repos Tab ── */}
        {activeTab === 'repos' && (
          <>
            {reposLoading ? (
              <div className="vt323" style={{ fontSize: '1.5rem', textAlign: 'center', marginTop: '40px', color: '#666' }}>
                Fetching your GitHub repositories...
              </div>
            ) : repos.length === 0 ? (
              <div className="pixel-border" style={{ padding: '40px', textAlign: 'center', background: '#fff' }}>
                <GitHubIcon sx={{ fontSize: '4rem', color: '#ccc', mb: 2 }} />
                <div className="vt323" style={{ fontSize: '2rem', color: '#666' }}>NO REPOS FOUND</div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {repos.map(repo => {
                  const langColor = LANG_COLORS[repo.language] || '#888';
                  const pushedDate = repo.pushed_at ? new Date(repo.pushed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Never';

                  return (
                    <div key={repo.id} className="pixel-border" style={{ background: '#fff', padding: '20px', display: 'flex', flexDirection: 'column', gap: 12, cursor: 'pointer', transition: 'box-shadow 0.2s' }}
                      onClick={() => navigate(`/repo/${repo.name}`)}
                    >
                      {/* Repo Name + Visibility */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <GitHubIcon fontSize="small" />
                          <span className="vt323" style={{ fontSize: '1.4rem', letterSpacing: 1, color: '#0969DA' }}>
                            {repo.name}
                          </span>
                        </div>
                        <div className="vt323" style={{
                          fontSize: '0.85rem', padding: '2px 8px',
                          border: `2px solid ${repo.private ? '#cf222e' : '#2da44e'}`,
                          color: repo.private ? '#cf222e' : '#2da44e',
                          display: 'flex', alignItems: 'center', gap: 4,
                        }}>
                          {repo.private ? <><LockIcon sx={{ fontSize: 12 }} /> PRIVATE</> : <><PublicIcon sx={{ fontSize: 12 }} /> PUBLIC</>}
                        </div>
                      </div>

                      {/* Description */}
                      {repo.description && (
                        <div style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#555', lineHeight: 1.5 }}>
                          {repo.description.substring(0, 100)}
                        </div>
                      )}

                      {/* Stats row */}
                      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'monospace', fontSize: '0.8rem', color: '#666' }}>
                          <span style={{ width: 10, height: 10, borderRadius: '50%', background: langColor, display: 'inline-block' }} />
                          {repo.language}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'monospace', fontSize: '0.8rem', color: '#666' }}>
                          <StarIcon sx={{ fontSize: 14 }} /> {repo.stargazers_count}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'monospace', fontSize: '0.8rem', color: '#666' }}>
                          <ForkIcon sx={{ fontSize: 14 }} /> {repo.forks_count}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'monospace', fontSize: '0.8rem', color: '#666' }}>
                          <TimeIcon sx={{ fontSize: 14 }} /> Pushed {pushedDate}
                        </span>
                      </div>

                      {/* Actions */}
                      <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                        <a
                          href={repo.html_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ textDecoration: 'none', flex: 1 }}
                          onClick={e => e.stopPropagation()}
                        >
                          <button className="pixel-button" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: '0.9rem', padding: '6px 12px' }}>
                            <LinkIcon fontSize="small" /> VIEW ON GITHUB
                          </button>
                        </a>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* ── Guardian Logs Tab ── */}
        {activeTab === 'logs' && (
          <>
            {logsLoading ? (
              <div className="vt323" style={{ fontSize: '1.5rem', textAlign: 'center', marginTop: '40px', color: '#666' }}>
                Loading push logs...
              </div>
            ) : guardianLogs.length === 0 ? (
              <div className="pixel-border" style={{ padding: '40px', textAlign: 'center', background: '#fff' }}>
                <HistoryIcon sx={{ fontSize: '4rem', color: '#ccc', mb: 2 }} />
                <div className="vt323" style={{ fontSize: '2rem', color: '#666' }}>NO GUARDIAN PUSHES YET</div>
                <div className="vt323" style={{ fontSize: '1.2rem', color: '#999', marginTop: 10 }}>
                  Use the Desktop Wizard to create or sync repositories.
                </div>
                <button className="pixel-button primary" style={{ marginTop: 24 }} onClick={() => navigate('/desktop')}>
                  GO TO DESKTOP
                </button>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '16px' }}>
                {guardianLogs.map(item => {
                  const date = new Date(item.created_at).toLocaleString();
                  let statusColor = '#666';
                  let StatusIcon = HistoryIcon;
                  let statusText = 'UNKNOWN';

                  if (item.status === 'auto_merged') { statusColor = '#8250df'; StatusIcon = MergeIcon; statusText = 'AUTO MERGED'; }
                  else if (item.status === 'pr_created') { statusColor = '#0969DA'; StatusIcon = PushIcon; statusText = 'PR OPENED'; }
                  else if (item.status === 'success') { statusColor = '#2da44e'; StatusIcon = PushIcon; statusText = 'REPO CREATED'; }
                  else if (item.status === 'error') { statusColor = '#cf222e'; StatusIcon = ErrorIcon; statusText = 'FAILED'; }

                  return (
                    <div key={item.id} className="pixel-border" style={{ background: '#fff', padding: '20px', display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
                      <div style={{ background: statusColor + '20', padding: 12, borderRadius: 4 }}>
                        <StatusIcon sx={{ fontSize: '2rem', color: statusColor }} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                          <div className="vt323" style={{ fontSize: '1.5rem', letterSpacing: 1 }}>{item.repository_name}</div>
                          <div className="vt323" style={{
                            color: statusColor, border: `2px solid ${statusColor}`,
                            padding: '2px 8px', fontSize: '0.9rem', background: statusColor + '10'
                          }}>
                            {statusText}
                          </div>
                        </div>
                        <div className="vt323" style={{ fontSize: '1.1rem', color: '#444', marginBottom: 12 }}>
                          "{item.commit_message}"
                        </div>
                        <div style={{ display: 'flex', gap: 20, color: '#666', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><TimeIcon fontSize="small" /> {date}</span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><GitHubIcon fontSize="small" /> {item.branch_name}</span>
                        </div>
                        {item.status === 'error' && (
                          <div className="vt323" style={{ marginTop: 12, color: '#cf222e', fontSize: '0.9rem' }}>
                            Error: {item.log_details?.substring(0, 120)}...
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
