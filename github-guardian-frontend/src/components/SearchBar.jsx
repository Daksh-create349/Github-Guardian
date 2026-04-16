import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, TextField, Button } from '@mui/material';

export default function SearchBar() {
  const [repo, setRepo] = useState('');
  const navigate = useNavigate();

  const handleSearch = () => {
    let input = repo.trim();
    
    // 1. Handle full GitHub URLs
    if (input.includes('github.com/')) {
      input = input.split('github.com/')[1];
    }
    
    // 2. Remove .git extension if present
    if (input.endsWith('.git')) {
      input = input.slice(0, -4);
    }
    
    // 3. Split and trim parts
    const parts = input.split('/').map(p => p.trim()).filter(p => p.length > 0);
    
    if (parts.length >= 2) {
      const owner = parts[0];
      const name = parts[1];
      navigate(`/dashboard/${owner}/${name}`);
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <TextField 
        label="Owner/Repo" 
        variant="outlined" 
        value={repo} 
        onChange={(e) => setRepo(e.target.value)} 
      />
      <Button variant="contained" onClick={handleSearch}>Scan</Button>
    </Box>
  )
}
