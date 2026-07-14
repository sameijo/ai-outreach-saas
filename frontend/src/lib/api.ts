/**
 * API client for communicating with the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      // Try refresh
      const refreshed = await this.tryRefresh();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.token}`;
        const retryRes = await fetch(`${API_BASE}${path}`, { ...options, headers });
        if (!retryRes.ok) throw new Error(`API error: ${retryRes.status}`);
        return retryRes.json();
      }
      this.clearToken();
      window.location.href = '/auth/login';
      throw new Error('Unauthorized');
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `API error: ${res.status}`);
    }

    return res.json();
  }

  private async tryRefresh(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      this.setToken(data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // Auth
  async register(email: string, password: string, fullName: string, company: string) {
    const data = await this.request<any>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, company }),
    });
    this.setToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async login(email: string, password: string) {
    const data = await this.request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async getMe() { return this.request<any>('/auth/me'); }

  // Dashboard
  async getDashboardOverview(days = 30) { return this.request<any>(`/dashboard/overview?days=${days}`); }
  async getDashboardActivity(days = 30) { return this.request<any>(`/dashboard/activity?days=${days}`); }
  async getCampaignsSummary() { return this.request<any>('/dashboard/campaigns/summary'); }
  async exportLeads(listId?: number) { return this.request<any>(`/dashboard/export/csv${listId ? `?list_id=${listId}` : ''}`); }

  // Leads
  async getLeadLists(skip = 0, limit = 20) { return this.request<any[]>(`/leads/lists?skip=${skip}&limit=${limit}`); }
  async getLeadList(id: number) { return this.request<any>(`/leads/lists/${id}`); }
  async searchLeads(query: string, source = 'apollo', limit = 50) {
    return this.request<any>('/leads/search', {
      method: 'POST',
      body: JSON.stringify({ query, source, limit }),
    });
  }
  async uploadCSV(file: File, listName: string) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/leads/upload-csv?list_name=${encodeURIComponent(listName)}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${this.token}` },
      body: formData,
    });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  }
  async enrichLeads(leadIds: number[], tone = 'professional') {
    return this.request<any>('/leads/enrich', {
      method: 'POST',
      body: JSON.stringify({ lead_ids: leadIds, tone }),
    });
  }
  async verifyLeads(leadIds: number[]) {
    return this.request<any>('/leads/verify', {
      method: 'POST',
      body: JSON.stringify(leadIds),
    });
  }
  async deleteLeadList(id: number) { return this.request<any>(`/leads/lists/${id}`, { method: 'DELETE' }); }

  // Campaigns
  async getCampaigns(status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request<any[]>(`/campaigns${params}`);
  }
  async getCampaign(id: number) { return this.request<any>(`/campaigns/${id}`); }
  async createCampaign(data: any) { return this.request<any>('/campaigns', { method: 'POST', body: JSON.stringify(data) }); }
  async updateCampaign(id: number, data: any) { return this.request<any>(`/campaigns/${id}`, { method: 'PATCH', body: JSON.stringify(data) }); }
  async deleteCampaign(id: number) { return this.request<any>(`/campaigns/${id}`, { method: 'DELETE' }); }
  async startCampaign(id: number) { return this.request<any>(`/campaigns/${id}/start`, { method: 'POST' }); }
  async pauseCampaign(id: number) { return this.request<any>(`/campaigns/${id}/pause`, { method: 'POST' }); }
  async resumeCampaign(id: number) { return this.request<any>(`/campaigns/${id}/resume`, { method: 'POST' }); }
  async getCampaignStats(id: number) { return this.request<any>(`/campaigns/${id}/stats`); }
  async getCampaignEvents(id: number, status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request<any[]>(`/campaigns/${id}/events${params}`);
  }

  // SMTP Configs
  async getSmtpConfigs() { return this.request<any[]>('/campaigns/smtp-configs/list'); }
  async createSmtpConfig(data: any) { return this.request<any>('/campaigns/smtp-configs', { method: 'POST', body: JSON.stringify(data) }); }
  async deleteSmtpConfig(id: number) { return this.request<any>(`/campaigns/smtp-configs/${id}`, { method: 'DELETE' }); }
}

export const api = new ApiClient();
