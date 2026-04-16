import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Grid, Paper, Tabs, Tab, Button, Divider } from '@mui/material';
import { BarChart } from '@mui/x-charts/BarChart';
import { client } from '../api/client';
import OverviewCard from '../components/OverviewCard';
import SecurityScore from '../components/SecurityScore';
import ScanButton from '../components/ScanButton';
import FindingsTable from '../components/FindingsTable';
import AIInsightModal from '../components/AIInsightModal';

const SCAN_STEPS = [
  "Cloning and scanning full git history...",
  "Performing Semantic Code Audit (SQLi, XSS)...",
  "Generating AI-driven Code Review...",
  "Analyzing commit history for 'oops' patterns...",
  "Auditing CI/CD & Dependencies...",
  "Generating Supply Chain SBOM (Grype/Syft)...",
  "Finalizing Security Permissions Audit...",
  "Generating FINAL Guardian Audit Report..."
];

export default function DashboardPage() {
  const { owner, repo } = useParams();
  const [status, setStatus] = useState('idle');
  const [findings, setFindings] = useState(null);
  const [overview, setOverview] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedInsight, setSelectedInsight] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [report, setReport] = useState(null);

  useEffect(() => {
    if (owner && repo) {
      client.get(`/repo/${owner}/${repo}/overview`).then(res => setOverview(res.data)).catch(() => {});
    }
  }, [owner, repo]);

  const startScan = async () => {
    setStatus('scanning');
    setFindings(null);
    setReport(null);
    try {
      const { data } = await client.post('/scan', { owner, repo_name: repo });
      pollStatus(data.task_id);
    } catch (e) { setStatus('error'); }
  };

  const pollStatus = async (taskId) => {
    const inter = setInterval(async () => {
      try {
        const { data } = await client.get(`/scan/status/${taskId}`);
        if (data.message) setProgressMessage(data.message);
        if (data.status === 'completed') {
          clearInterval(inter);
          setFindings(data.result || {});
          setReport(data.report || null);
          setStatus('done');
          setProgressMessage('');
        } else if (data.status === 'failed') {
          clearInterval(inter);
          setStatus('error');
        }
      } catch (err) { clearInterval(inter); setStatus('error'); }
    }, 2000);
  };

  const currentStepIndex = SCAN_STEPS.indexOf(progressMessage);

  return (
    <Box p={4} sx={{ color: '#000', minHeight: '100vh', bgcolor: '#FFF' }}>
      <Grid container spacing={4}>
        <Grid item xs={12} md={8}>
          <Typography variant="h3" className="vt323" sx={{ mb: 1 }}>GUARDIAN AUDIT: {owner}/{repo}</Typography>
          <OverviewCard data={overview} />
        </Grid>
        <Grid item xs={12} md={4} textAlign="center">
          <Box sx={{ minHeight: 250, display: 'flex', flexDirection: 'column', alignItems: 'center', p: 2 }}>
            {report && <SecurityScore score={report.score} />}
            <ScanButton status={status} onScan={startScan} />
            
            {status === 'scanning' && (
              <Box mt={4} sx={{ textAlign: 'left', width: '100%' }}>
                <Typography variant="h6" className="vt323" color="primary">LIVE SCAN PROGRESS</Typography>
                <Box className="pixel-border" sx={{ p: 2, bgcolor: '#F8F8F8' }}>
                    {SCAN_STEPS.slice(0, currentStepIndex + 1).map((step, i) => (
                    <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" className="vt323">
                          {i < currentStepIndex ? (
                            <span className="status-done">DONE </span>
                          ) : (
                            <span className="pixel-spinner"></span>
                          )}
                          <span style={{ color: i < currentStepIndex ? '#2da44e' : '#000' }}> {step.toUpperCase()}</span>
                        </Typography>
                    </Box>
                    ))}
                </Box>
              </Box>
            )}
          </Box>
        </Grid>

        {report && (
          <Grid item xs={12}>
            <Paper className="pixel-border" sx={{ p: 4, bgcolor: '#FFFFFF', color: '#000' }}>
              <Typography variant="h4" className="vt323" color="primary.main" gutterBottom>SECURITY REPORT CARD</Typography>
              <Typography variant="h5" className="vt323" sx={{ fontStyle: 'italic', mb: 3 }}>"{report.verdict}"</Typography>
              <Grid container spacing={4}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" className="vt323" sx={{ color: '#2da44e', mb: 2, borderBottom: '2px solid #000' }}>POSITIVE FINDINGS</Typography>
                  {report.positives.map((p, i) => <Typography key={i} variant="body1" className="vt323" sx={{ mb: 1 }}><span style={{color: '#2da44e'}}>PASS</span> | {p.toUpperCase()}</Typography>)}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" className="vt323" sx={{ color: '#cf222e', mb: 2, borderBottom: '2px solid #000' }}>RISK MITIGATIONS</Typography>
                  {report.negatives.map((n, i) => <Typography key={i} variant="body1" className="vt323" sx={{ mb: 1 }}><span style={{color: '#cf222e'}}>RISK</span> | {n.toUpperCase()}</Typography>)}
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        )}

        {findings && (
          <Grid item xs={12}>
            <Box className="pixel-border" sx={{ bgcolor: '#F0F0F0' }}>
              <Tabs 
                value={activeTab} 
                onChange={(e, v) => setActiveTab(v)} 
                textColor="inherit" 
                indicatorColor="primary"
                sx={{ borderBottom: '2px solid #000' }}
              >
                <Tab className="vt323" sx={{ fontSize: '1.2rem'}} label={`VULNS (${findings.sast_findings?.length || 0})`} />
                <Tab className="vt323" sx={{ fontSize: '1.2rem'}} label={`SECRETS (${findings.secret_findings?.length || 0})`} />
                <Tab className="vt323" sx={{ fontSize: '1.2rem'}} label="CODE REVIEW" />
                <Tab className="vt323" sx={{ fontSize: '1.2rem'}} label="SUPPLY CHAIN" />
                <Tab className="vt323" sx={{ fontSize: '1.2rem'}} label="AUDIT LOG" />
              </Tabs>

              <Box sx={{ bgcolor: '#FFF', p: 3 }}>
                {activeTab === 0 && (
                  <FindingsTable 
                    rows={(findings.sast_findings || []).map((f, i) => ({id: i, ...f}))} 
                    columns={[
                      { field: 'type', headerName: 'ISSUE', width: 250 },
                      { field: 'file', headerName: 'LOCATION', width: 200 },
                      { field: 'severity', headerName: 'LEVEL', width: 120 },
                      { field: 'ai', headerName: 'ACTION', width: 120, renderCell: (p) => <button className="pixel-button" style={{fontSize: '0.8rem', padding: '5px 10px'}} onClick={() => { setSelectedInsight(p.row.ai_insight); setModalOpen(true); }}>ANALYSIS</button> }
                    ]} 
                  />
                )}
                {activeTab === 1 && (
                  <FindingsTable 
                    rows={(findings.secret_findings || []).map((f, i) => ({id: i, ...f}))} 
                    columns={[
                      { field: 'pattern_matched', headerName: 'LEAK TYPE', width: 200 },
                      { field: 'commit_sha', headerName: 'LOCATOR', width: 200 },
                      { field: 'ai', headerName: 'ACTION', width: 120, renderCell: (p) => <button className="pixel-button" style={{fontSize: '0.8rem', padding: '5px 10px'}} onClick={() => { setSelectedInsight(p.row.ai_insight); setModalOpen(true); }}>ANALYSIS</button> }
                    ]} 
                  />
                )}
                {activeTab === 2 && (
                  <Box sx={{ color: '#000', whiteSpace: 'pre-wrap', fontFamily: 'monospace', p: 2 }}>
                    <Typography variant="h5" className="vt323" color="primary" gutterBottom>ARCHITECTURAL REVIEW</Typography>
                    <Typography variant="body2" className="vt323" sx={{ mb: 2 }}>STRATEGY: DEEP ARCHITECTURAL INSPECTION</Typography>
                    <Box sx={{ height: '2px', bgcolor: '#000', mb: 3 }} />
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                        {report.code_review?.detailed_review || "AI analysis in progress..."}
                    </Typography>
                  </Box>
                )}
                {activeTab === 3 && (
                  <Box p={5} textAlign="center" sx={{ bgcolor: '#FFF' }}>
                    <BarChart
                      xAxis={[{ scaleType: 'band', data: ['CRIT', 'HIGH', 'MED', 'LOW'] }]}
                      series={[{ data: [findings.supply_chain?.summary?.critical || 0, findings.supply_chain?.summary?.high || 0, findings.supply_chain?.summary?.medium || 0, findings.supply_chain?.summary?.low || 0], color: '#0969DA' }]}
                      width={600} height={350}
                    />
                  </Box>
                )}
                {activeTab === 4 && (
                  <Box p={3}>
                    <Typography variant="h6" className="vt323" gutterBottom>GUARDIAN VERIFICATION LOG</Typography>
                    {report.audit_summary?.map((c, i) => <Typography key={i} variant="body2" className="vt323">✅ {c.toUpperCase()}</Typography>)}
                  </Box>
                )}
              </Box>
            </Box>
          </Grid>
        )}
      </Grid>
      <AIInsightModal open={modalOpen} handleClose={() => setModalOpen(false)} insight={selectedInsight} />
    </Box>
  );
}
