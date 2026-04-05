const API_BASE = process.env.REACT_APP_API_URL || '/api';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken() {
    return this.token;
  }

  isAuthenticated() {
    return !!this.token;
  }

  async request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (response.status === 401) {
      this.setToken(null);
      throw new Error('Authentication required');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // Auth
  async register(email, password, name, role = 'team_member') {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name, role }),
    });
    this.setToken(data.token);
    return data;
  }

  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.token);
    return data;
  }

  async getMe() {
    return this.request('/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // Progress
  async getProgress() {
    return this.request('/progress');
  }

  async completeModule(moduleKey, programme = 'onboarding') {
    return this.request('/progress/complete-module', {
      method: 'POST',
      body: JSON.stringify({ module_key: moduleKey, programme }),
    });
  }

  async saveQuizResult(moduleKey, score, total, answers = {}, programme = 'onboarding') {
    return this.request('/progress/quiz-result', {
      method: 'POST',
      body: JSON.stringify({ module_key: moduleKey, programme, score, total, answers }),
    });
  }

  async addTime(minutes) {
    return this.request('/progress/add-time', {
      method: 'POST',
      body: JSON.stringify(minutes),
    });
  }

  // Leaderboard
  async getLeaderboard() {
    return this.request('/leaderboard');
  }

  // Manager
  async getTeamStats() {
    return this.request('/manager/team-stats');
  }
}

const api = new ApiService();
export default api;
