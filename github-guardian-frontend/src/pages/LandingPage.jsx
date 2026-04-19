import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Container, Paper } from '@mui/material';
import { GitHub as GitHubIcon } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_AUTH_LOGIN_URL } from '../api/config';

export default function LandingPage() {
  const [url, setUrl] = useState('');
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleGitHubLogin = () => {
    window.location.href = API_AUTH_LOGIN_URL;
  };

  const handleScan = () => {
    if (!url) return;
    const parts = url.replace('https://github.com/', '').split('/');
    if (parts.length >= 2) {
      navigate(`/dashboard/${parts[0]}/${parts[1].replace('.git', '')}`);
    }
  };

  return (
    <Box sx={{ position: 'relative',

      minHeight: '100vh', 
      bgcolor: '#FFF', 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center',
      p: 4
    }}>
      {/* Static Mascot */}
      <Box sx={{ 
        position: 'relative', mb: 4, width: 220, height: 220, 
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}>
        <img 
          src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAwUlEQVR4nO2XsRLDMAhDLV3+/5fduw4dKMbgEOhQjSTo6RziOBhxzc11RMyQBD32x0NgN4cFcNOLBXDTk0XwpTcL4SoDGzgOA3r63vdcTsOV8W2xcOml5u41LBG7A8BYfnTtA6ViLe4f4FsczeIvB5hV5wGMPmH3CDJWwfTgoi4/0ydBXH0QDbIe3aYjQeE5E2oga2bC80SjWQuRNbAfH64uKPV0uBYgawBdcLUg4C6TO300jDI3qKXX5Wx87Oe0XS82cCQ5DhANRQAAAABJRU5ErkJggg==" 
          alt="Pixel GitHub Logo"
          style={{ width: '220px', height: '220px', imageRendering: 'pixelated', filter: 'drop-shadow(6px 6px 0px rgba(0,0,0,0.2))' }}
        />
      </Box>

      {/* Auth bar — top right */}
      <Box sx={{ position: 'absolute', top: 20, right: 28, display: 'flex', alignItems: 'center', gap: 1 }}>
        {user ? (
          <>
            <img src={user.avatar_url} alt={user.username}
              style={{ width: 34, height: 34, borderRadius: '50%', border: '2px solid #000' }} />
            <Typography className="vt323" sx={{ fontSize: '1.1rem' }}>@{user.username}</Typography>
            <button className="pixel-button" style={{ fontSize: '0.9rem', padding: '4px 12px' }} onClick={logout}>
              LOGOUT
            </button>
          </>
        ) : (
          <button
            onClick={handleGitHubLogin}
            style={{
              border: '3px solid #000', background: '#000', color: '#fff',
              padding: '8px 18px', fontFamily: "'VT323', monospace",
              fontSize: '1.1rem', cursor: 'pointer', letterSpacing: 2,
              display: 'flex', alignItems: 'center', gap: '8px',
            }}
          >
            <GitHubIcon sx={{ fontSize: 20 }} /> SIGN IN WITH GITHUB
          </button>
        )}
      </Box>

      <Container maxWidth="sm" sx={{ textAlign: 'center' }}>
        <Typography variant="h2" className="vt323" sx={{ mb: 1, letterSpacing: 4, fontWeight: 'bold' }}>
          REPOSITORY AUDIT
        </Typography>
        <Typography variant="body1" className="vt323" sx={{ mb: 4, opacity: 0.8, fontSize: '1.4rem' }}>
          DEEP FORENSIC SECURITY FOR THE MODERN REPOSITORY
        </Typography>

        <Paper 
          className="pixel-border"
          sx={{ 
            p: 1, 
            display: 'flex', 
            alignItems: 'center', 
            bgcolor: '#FFF',
            border: '3px solid #000 !important',
            mb: 4
          }}
        >
          <input
            className="vt323"
            placeholder="HTTPS://GITHUB.COM/USER/REPO"
            style={{ 
              flex: 1, 
              border: 'none', 
              padding: '15px', 
              outline: 'none', 
              background: 'transparent',
              fontSize: '1.6rem'
            }}
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleScan()}
          />
          <button 
            className="pixel-button primary"
            onClick={handleScan}
            style={{ height: '100%', fontSize: '1.4rem' }}
          >
            EXECUTE
          </button>
        </Paper>

        {/* GitHub Desktop CTA */}
        <div
          onClick={() => navigate('/desktop')}
          style={{
            border: '3px solid #000', padding: '20px 28px', marginBottom: '32px',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '20px',
            background: '#F8F8F8', transition: 'background 0.15s',
            boxShadow: '4px 4px 0px #000'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#EFF6FF';
            e.currentTarget.style.transform = 'translate(2px, 2px)';
            e.currentTarget.style.boxShadow = '2px 2px 0px #000';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#F8F8F8';
            e.currentTarget.style.transform = 'none';
            e.currentTarget.style.boxShadow = '4px 4px 0px #000';
          }}
        >
          <GitHubIcon sx={{ fontSize: '3rem' }} />
          <div style={{ textAlign: 'left', flex: 1 }}>
            <div style={{ fontFamily: "'VT323', monospace", fontSize: '1.6rem', letterSpacing: 3 }}>
              GITHUB DESKTOP
            </div>
            <div style={{ fontFamily: "'VT323', monospace", fontSize: '1.1rem', opacity: 0.7 }}>
              CREATE REPO · DRAG & DROP FILES · AUTO .GITIGNORE · PUSH IN ONE CLICK
            </div>
          </div>
          <span style={{ fontFamily: "'VT323', monospace", fontSize: '1.5rem', opacity: 0.7 }}>→</span>
        </div>

        <Box sx={{ mt: 8, display: 'flex', gap: 6, justifyContent: 'center' }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" className="vt323" sx={{ mb: 0.5 }}>FORENSICS</Typography>
            <Typography variant="caption" className="vt323" sx={{ fontSize: '0.9rem' }}>0-DAY LEAK DETECTION</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" className="vt323" sx={{ mb: 0.5 }}>SBOM</Typography>
            <Typography variant="caption" className="vt323" sx={{ fontSize: '0.9rem' }}>SUPPLY CHAIN VETTING</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" className="vt323" sx={{ mb: 0.5 }}>CI/CD</Typography>
            <Typography variant="caption" className="vt323" sx={{ fontSize: '0.9rem' }}>PIPELINE HYGIENE</Typography>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}
