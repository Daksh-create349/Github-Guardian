import { Box, Typography } from '@mui/material';

export default function ScanButton({ status, onScan }) {
  if (status === 'scanning') {
    return (
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="h6" className="vt323" sx={{ animation: 'blink 1s infinite' }}>
          SCANNING CODEX...
        </Typography>
      </Box>
    );
  }

  return (
    <button 
      className="pixel-button primary" 
      onClick={onScan} 
      style={{ marginTop: '20px', width: '100%', maxWidth: '300px' }}
    >
      {status === 'idle' ? 'INITIATE FULL AUDIT' : 'RE-SCAN REPOSITORY'}
    </button>
  );
}
