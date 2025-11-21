import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
});

// Targets
export const fetchTargets = async () => {
  const { data } = await api.get('/api/targets');
  return data;
};

export const createTarget = async (target) => {
  const { data } = await api.post('/api/targets', target);
  return data;
};

export const createTargetFromGitHub = async (githubUrl) => {
  const { data } = await api.post('/api/targets/from-github', { github_url: githubUrl });
  return data;
};

export const updateTarget = async (id, updates) => {
  const { data } = await api.put(`/api/targets/${id}`, updates);
  return data;
};

export const deleteTarget = async (id) => {
  await api.delete(`/api/targets/${id}`);
};

// Pentest Runs
export const startScan = async (targetId) => {
  const { data } = await api.post(`/api/targets/${targetId}/scan`);
  return data;
};

export const fetchRuns = async () => {
  const { data } = await api.get('/api/runs');
  return data;
};

export const fetchRunDetails = async (runId) => {
  const { data } = await api.get(`/api/runs/${runId}`);
  return data;
};

export const fetchRunStatus = async (runId) => {
  const { data } = await api.get(`/api/runs/${runId}/status`);
  return data;
};

// Vulnerabilities
export const fetchVulnerabilities = async () => {
  const { data } = await api.get('/api/vulnerabilities');
  return data;
};

export const updateVulnerability = async (id, updates) => {
  const { data } = await api.put(`/api/vulnerabilities/${id}`, updates);
  return data;
};

// Analytics
export const fetchOverview = async () => {
  const { data } = await api.get('/api/analytics/overview');
  return data;
};

export const fetchTrends = async (days = 30) => {
  const { data } = await api.get(`/api/analytics/trends?days=${days}`);
  return data;
};
