import { createContext, useContext, useState, useEffect } from 'react';
import { client } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);      // { username, name, avatar_url }
  const [loading, setLoading] = useState(true); // true while we verify the stored token

  // On app load: check if a token is already stored and still valid
  useEffect(() => {
    const token = localStorage.getItem('gh_guardian_token');
    if (token) {
      client.get('/auth/me')
        .then((res) => setUser(res.data))
        .catch(() => {
          // Token expired or invalid — clean up
          localStorage.removeItem('gh_guardian_token');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  /**
   * Called by AuthCallbackPage after receiving the JWT from the backend.
   * Stores the token and fetches user info.
   */
  const login = async (token) => {
    localStorage.setItem('gh_guardian_token', token);
    try {
      const res = await client.get('/auth/me');
      setUser(res.data);
    } catch {
      localStorage.removeItem('gh_guardian_token');
    }
  };

  const logout = () => {
    localStorage.removeItem('gh_guardian_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
