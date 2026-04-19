import axios from 'axios';
import { API_BASE_URL } from './config';

export const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
});

// Automatically attach JWT to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('gh_guardian_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
