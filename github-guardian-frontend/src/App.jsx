import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import LandingPage from './pages/LandingPage';
import GithubDesktopPage from './pages/GithubDesktopPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard/:owner/:repo" element={<DashboardPage />} />
          <Route path="/desktop" element={<GithubDesktopPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
export default App;
