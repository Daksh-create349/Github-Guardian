import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';

export default function OverviewCard({ data }) {
  const [loadingDots, setLoadingDots] = useState('');

  useEffect(() => {
    if (!data) {
      const interval = setInterval(() => {
        setLoadingDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
      }, 500);
      return () => clearInterval(interval);
    }
  }, [data]);

  if (!data) {
    return (
      <Box className="pixel-border" sx={{ p: 3, mb: 3, bgcolor: '#FFF', color: '#000', minHeight: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
        <Typography variant="h4" className="vt323" sx={{ mb: 2 }}>ACCESSING MAINFRAME</Typography>
        <Typography variant="h5" className="vt323" sx={{ color: '#0969DA', display: 'flex', alignItems: 'center', gap: 2 }}>
           <span className="pixel-spinner"></span> FETCHING REPOSITORY TELEMETRY{loadingDots}
        </Typography>
      </Box>
    );
  }

  return (
    <Box className="pixel-border" sx={{ p: 3, mb: 3, bgcolor: '#FFF', color: '#000' }}>
        <Typography variant="h4" className="vt323" gutterBottom>{data.name?.toUpperCase()}</Typography>
        <Typography variant="body1" className="vt323" sx={{ opacity: 0.8 }}>{data.description}</Typography>
        <Box sx={{ mt: 2, display: 'flex', gap: 3 }}>
            <Typography variant="body2" className="vt323">STARS: {data.stars}</Typography>
            <Typography variant="body2" className="vt323">FORKS: {data.forks}</Typography>
            <Typography variant="body2" className="vt323">TECH: {data.language?.toUpperCase()}</Typography>
        </Box>
    </Box>
  );
}
