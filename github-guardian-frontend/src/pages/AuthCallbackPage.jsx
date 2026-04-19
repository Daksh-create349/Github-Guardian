import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { GitHub as GitHubIcon } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

/**
 * This page handles the redirect from our backend after GitHub OAuth.
 * URL looks like: /auth/callback?token=<JWT>
 * We grab the token, save it, and redirect to /desktop.
 */
export default function AuthCallbackPage() {
  const [params] = useSearchParams();
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const token = params.get('token');
    if (token) {
      login(token).then(() => {
        navigate('/desktop', { replace: true });
      });
    } else {
      // No token — something went wrong with OAuth
      navigate('/', { replace: true });
    }
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'VT323', monospace",
      background: '#fff',
      gap: '16px',
    }}>
      <GitHubIcon sx={{ fontSize: '4rem' }} />
      <div style={{ fontSize: '2rem', letterSpacing: 4 }}>SIGNING YOU IN...</div>
      <div style={{ fontSize: '1.1rem', color: '#666' }}>
        Verifying your GitHub identity. Hold tight!
      </div>
      <div style={{
        width: '200px', height: '6px', background: '#eee',
        border: '2px solid #000', overflow: 'hidden', marginTop: '8px',
      }}>
        <div style={{
          height: '100%',
          background: '#0969DA',
          animation: 'slide 1.2s ease-in-out infinite',
          width: '60%',
        }} />
      </div>
      <style>{`
        @keyframes slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>
    </div>
  );
}
