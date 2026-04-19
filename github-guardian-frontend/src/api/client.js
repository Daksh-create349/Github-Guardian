import axios from 'axios';

export const client = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '') + '/api/v1',
});

// Automatically attach JWT to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('gh_guardian_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
