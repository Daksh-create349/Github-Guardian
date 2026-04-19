/**
 * Central API config.
 * - Locally:      falls back to http://localhost:8000
 * - Deployed:     uses the VITE_API_BASE_URL env var set on Vercel
 *
 * Set VITE_API_BASE_URL=https://your-backend.onrender.com in Vercel's
 * Environment Variables panel. No code change needed ever again.
 */
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
).replace(/\/$/, '');

/** Full base for direct browser redirects (OAuth login etc.) */
export const API_AUTH_LOGIN_URL = `${API_BASE_URL}/api/v1/auth/login`;
