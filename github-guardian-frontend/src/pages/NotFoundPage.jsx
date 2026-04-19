import { useNavigate } from 'react-router-dom';
import { ArrowBack as ArrowLeftIcon } from '@mui/icons-material';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      background: '#fff',
      color: '#000',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      textAlign: 'center'
    }}>
      <div className="vt323" style={{ fontSize: '10rem', color: '#cf222e', lineHeight: 1, marginBottom: 10 }}>
        404
      </div>
      
      <div className="vt323" style={{ fontSize: '2rem', marginBottom: '20px' }}>
        YOU WANDERED OFF THE MAP!
      </div>
      
      <div className="vt323" style={{ fontSize: '1.2rem', color: '#666', maxWidth: '400px', marginBottom: '30px' }}>
        It's dangerous to go alone into unknown routes! Take this button to go back.
      </div>

      <button 
        className="pixel-button primary" 
        onClick={() => navigate('/')}
        style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}
      >
        <ArrowLeftIcon fontSize="small" /> TELEPORT HOME
      </button>
    </div>
  );
}
