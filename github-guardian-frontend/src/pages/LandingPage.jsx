import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Container, Paper } from '@mui/material';
import octocatLogo from '../assets/octocat.png';

export default function LandingPage() {
  const [url, setUrl] = useState('');
  const navigate = useNavigate();

  const handleScan = () => {
    if (!url) return;
    const parts = url.replace('https://github.com/', '').split('/');
    if (parts.length >= 2) {
      navigate(`/dashboard/${parts[0]}/${parts[1].replace('.git', '')}`);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      bgcolor: '#FFF', 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center',
      p: 4
    }}>
      {/* Static Mascot */}
      <Box sx={{ position: 'relative', mb: 4, width: 220, height: 220 }}>
        <img 
          src={octocatLogo} 
          alt="Guardian Mascot" 
          style={{ width: '100%', height: '100%', imageRendering: 'pixelated' }} 
        />
      </Box>

      <Container maxWidth="sm" sx={{ textAlign: 'center' }}>
        <Typography variant="h2" className="vt323" sx={{ mb: 1, letterSpacing: 4, fontWeight: 'bold' }}>
          FORCED AUDIT
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
