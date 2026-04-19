import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import LandingPage from './pages/LandingPage';
import GithubDesktopPage from './pages/GithubDesktopPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import PushHistoryPage from './pages/PushHistoryPage';
import RepoDetailPage from './pages/RepoDetailPage';
import NotFoundPage from './pages/NotFoundPage';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard/:owner/:repo" element={<DashboardPage />} />
          <Route path="/desktop" element={<GithubDesktopPage />} />
          <Route path="/history" element={<PushHistoryPage />} />
          <Route path="/repo/:repoName" element={<RepoDetailPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
export default App;
