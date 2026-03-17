const API = '/api';

async function request(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API}${path}`, { ...options, headers });
  const data = res.status !== 204 ? await res.json() : null;
  if (!res.ok) throw { status: res.status, detail: data?.detail || 'Error' };
  return data;
}

export const api = {
  // Auth
  requestLink: (email, full_name) =>
    request('/auth/request-link', { method: 'POST', body: JSON.stringify({ email, full_name }) }),
  verify: (token) =>
    request('/auth/verify', { method: 'POST', body: JSON.stringify({ token }) }),

  // User
  getMe: () => request('/users/me'),

  // Onboarding
  submitOnboarding: (data) =>
    request('/onboarding/quiz', { method: 'POST', body: JSON.stringify(data) }),

  // Paths
  getPaths: (industry, level) => {
    const params = new URLSearchParams();
    if (industry) params.set('industry', industry);
    if (level) params.set('level', level);
    return request(`/paths/?${params}`);
  },

  // Lessons
  getLesson: (id) => request(`/lessons/${id}`),
  completeLesson: (id, data) =>
    request(`/lessons/${id}/complete`, { method: 'POST', body: JSON.stringify(data) }),

  // Modules
  getModule: (id) => request(`/modules/${id}`),

  // Gamification
  getLeaderboard: () => request('/gamification/leaderboard'),
  getBadges: () => request('/gamification/badges'),

  // Progress
  getProgress: () => request('/progress/me'),
  getMission: () => request('/progress/mission'),
  getCompanyWeekly: (companyId) => request(`/progress/company/${companyId}/weekly`),
};
