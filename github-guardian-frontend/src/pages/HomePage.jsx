import { Box, Typography } from '@mui/material';
import SearchBar from '../components/SearchBar';

export default function HomePage() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <Typography variant="h2" mb={4}>GitHub Guardian</Typography>
      <SearchBar />
    </Box>
  )
}
