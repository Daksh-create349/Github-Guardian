import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#000000', // High contrast black for pixel borders
    },
    background: {
      default: '#FFFFFF',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#000000',
    }
  },
  typography: {
    fontFamily: '"Segoe UI", "VT323", monospace',
  },
  shape: {
    borderRadius: 0, // Sharp pixel edges
  }
});
