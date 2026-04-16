import { AppBar as MUIAppBar, Toolbar, Typography } from '@mui/material';
export default function AppBar() {
  return (
    <MUIAppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>GitHub Guardian</Typography>
      </Toolbar>
    </MUIAppBar>
  );
}
