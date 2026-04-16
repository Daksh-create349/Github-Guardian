import { Modal, Box, Typography, Button } from '@mui/material';

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
