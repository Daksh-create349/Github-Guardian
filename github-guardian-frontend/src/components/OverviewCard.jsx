import { Box, Typography } from '@mui/material';

export default function OverviewCard({ data }) {
  if (!data) return null;
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
