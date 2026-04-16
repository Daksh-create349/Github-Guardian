import os

base_dir = "/Users/dakshsrivastava/Desktop/Crazy-ever/github-guardian-frontend"
os.chdir(base_dir)

frontend_files = {
    "src/components/OverviewCard.jsx": """import { Card, CardContent, Typography } from '@mui/material';

export default function OverviewCard({ data }) {
  if (!data) return null;
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>{data.name}</Typography>
        <Typography color="text.secondary">{data.description}</Typography>
        <Typography mt={1}>⭐ {data.stars} Stars</Typography>
      </CardContent>
    </Card>
  );
}
""",
    "src/components/SecurityScore.jsx": """import { Box, Typography, CircularProgress } from '@mui/material';

export default function SecurityScore({ score }) {
  return (
    <Box position="relative" display="inline-flex" my={2}>
      <CircularProgress variant="determinate" value={score * 10} size={80} color={score > 7 ? 'error' : 'success'} />
      <Box
        top={0} left={0} bottom={0} right={0}
        position="absolute" display="flex" alignItems="center" justifyContent="center"
      >
        <Typography variant="caption" component="div" color="text.secondary">
          {score}/10
        </Typography>
      </Box>
    </Box>
  );
}
""",
    "src/components/ScanButton.jsx": """import { Button, CircularProgress } from '@mui/material';

export default function ScanButton({ status, onScan }) {
  if (status === 'scanning') return <CircularProgress />;
  return (
    <Button variant="contained" color="primary" onClick={onScan} sx={{ mt: 2 }}>
      {status === 'idle' ? 'Run Full Security Audit' : 'Scan Again'}
    </Button>
  );
}
""",
    "src/components/FindingsTable.jsx": """import { DataGrid } from '@mui/x-data-grid';

export default function FindingsTable({ columns, rows }) {
  return (
    <div style={{ height: 400, width: '100%', marginTop: '20px' }}>
      <DataGrid rows={rows} columns={columns} pageSize={5} rowsPerPageOptions={[5]} />
    </div>
  );
}
""",
    "src/components/AIInsightModal.jsx": """import { Modal, Box, Typography, Button } from '@mui/material';

const style = {
  position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
  width: 400, bgcolor: 'background.paper', border: '2px solid #000', boxShadow: 24, p: 4,
};

export default function AIInsightModal({ open, handleClose, insight }) {
  if (!insight) return null;
  return (
    <Modal open={open} onClose={handleClose}>
      <Box sx={style}>
        <Typography variant="h6" component="h2">AI Interpreter Insight</Typography>
        <Typography sx={{ mt: 2 }} color="error">Severity: {insight.severity_score}/10</Typography>
        <Typography sx={{ mt: 2 }}>{insight.explanation}</Typography>
        <Typography sx={{ mt: 2 }} color="success.main">Fix: {insight.fix}</Typography>
        <Button onClick={handleClose} sx={{ mt: 3 }} variant="outlined">Close</Button>
      </Box>
    </Modal>
  );
}
""",
    "src/components/Layout/AppBar.jsx": """import { AppBar as MUIAppBar, Toolbar, Typography } from '@mui/material';
export default function AppBar() {
  return (
    <MUIAppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>GitHub Guardian</Typography>
      </Toolbar>
    </MUIAppBar>
  );
}
""",
    "src/components/Layout/Drawer.jsx": """import { Drawer as MUIDrawer, List, ListItem, ListItemText } from '@mui/material';
export default function Drawer() {
  return (
    <MUIDrawer variant="permanent" anchor="left" sx={{ width: 240, flexShrink: 0, '& .MuiDrawer-paper': { width: 240, boxSizing: 'border-box' } }}>
      <List>
        <ListItem button><ListItemText primary="Dashboard" /></ListItem>
      </List>
    </MUIDrawer>
  );
}
""",
    "src/components/Layout/ThemeToggle.jsx": """import { Button } from '@mui/material';
export default function ThemeToggle() {
  return <Button color="inherit">Toggle Theme</Button>;
}
""",
    "src/pages/DashboardPage.jsx": """import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import { client } from '../api/client';
import OverviewCard from '../components/OverviewCard';
import SecurityScore from '../components/SecurityScore';
import ScanButton from '../components/ScanButton';
import FindingsTable from '../components/FindingsTable';

export default function DashboardPage() {
  const { owner, repo } = useParams();
  const [status, setStatus] = useState('idle');
  const [findings, setFindings] = useState(null);
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    // Fetch Repo Overview on mount
    client.get(`/repo/${owner}/${repo}/overview`).then(res => setOverview(res.data)).catch(() => {});
  }, [owner, repo]);

  const startScan = async () => {
    setStatus('scanning');
    try {
      const { data } = await client.post('/scan', { owner, repo_name: repo });
      pollStatus(data.task_id);
    } catch (e) {
      setStatus('error');
    }
  };

  const pollStatus = async (taskId) => {
    const inter = setInterval(async () => {
      const { data } = await client.get(`/scan/status/${taskId}`);
      if (data.status === 'completed') {
        clearInterval(inter);
        setFindings(data.result);
        setStatus('done');
      }
    }, 2000);
  };

  const oopsColumns = [
    { field: 'commit_message', headerName: 'Commit', width: 200 },
    { field: 'sha', headerName: 'SHA', width: 150 },
    { field: 'ai_insight', headerName: 'AI Insight', width: 300, valueGetter: (params) => params.row.ai_insight?.explanation || '' }
  ];

  return (
    <Box p={4}>
      <Typography variant="h4" mb={2}>Dashboard: {owner}/{repo}</Typography>
      
      <OverviewCard data={overview} />
      
      {findings && <SecurityScore score={8.5} />}
      
      <ScanButton status={status} onScan={startScan} />
      
      {findings && (
        <Box mt={4}>
          <Typography variant="h5" mb={2}>Oops Commits Detected</Typography>
          <FindingsTable 
            rows={findings.oops_commits.map((o, i) => ({id: i, ...o}))} 
            columns={oopsColumns} 
          />
        </Box>
      )}
    </Box>
  );
}
"""
}

for filepath, content in frontend_files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

