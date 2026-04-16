import { Drawer as MUIDrawer, List, ListItem, ListItemText } from '@mui/material';
export default function Drawer() {
  return (
    <MUIDrawer variant="permanent" anchor="left" sx={{ width: 240, flexShrink: 0, '& .MuiDrawer-paper': { width: 240, boxSizing: 'border-box' } }}>
      <List>
        <ListItem button><ListItemText primary="Dashboard" /></ListItem>
      </List>
    </MUIDrawer>
  );
}
