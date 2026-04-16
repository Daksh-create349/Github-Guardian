import { Box, Typography } from '@mui/material';

export default function SecurityScore({ score }) {
  const getColor = (s) => {
    if (s <= 3) return '#2da44e'; // Green
    if (s <= 6) return '#e3b341'; // Yellow
    return '#cf222e'; // Red
  };

  const getLabel = (s) => {
    if (s <= 3) return 'SECURE';
    if (s <= 6) return 'CAUTION';
    return 'DANGER';
  };

  const barSegments = Array.from({ length: 10 }, (_, i) => i + 1);

  return (
    <Box display="flex" flexDirection="column" alignItems="center" my={2}>
      <Typography variant="h6" className="vt323" sx={{ color: getColor(score), mb: 1 }}>
        RISK LEVEL: {getLabel(score)} ({score}/10)
      </Typography>
      
      {/* Pixel Bar */}
      <Box 
        className="pixel-border"
        sx={{ 
          display: 'flex', 
          gap: 1, 
          p: 1, 
          bgcolor: '#FFF',
          width: 'fit-content'
        }}
      >
        {barSegments.map((segment) => (
          <Box
            key={segment}
            sx={{
              width: 25,
              height: 40,
              bgcolor: segment <= score ? getColor(score) : '#EEE',
              border: '2px solid #000',
              boxShadow: segment <= score ? 'inset 4px 4px 0px rgba(0,0,0,0.2)' : 'none'
            }}
          />
        ))}
      </Box>
    </Box>
  );
}
