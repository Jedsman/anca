import axios from 'axios';

// In Docker, the API is at standard port 8000 via proxy? 
// Or direct. If using Vite proxy: /api 
// We will configure Vite proxy.
const API_BASE = '/api/v1';

export interface GenerateRequest {
    topic: string;
    affiliate?: boolean;
    niche?: string; // Optional
    discover_mode?: boolean;
    provider?: string;
    model?: string;
    only_discovery?: boolean;
}

export interface DiscoverRequest {
    niche?: string;
    affiliate?: boolean;
    provider?: string;
    model?: string;
}

export interface PublishRequest {
    filename: string;
    wp_url: string;
    wp_user: string;
    wp_password: string;
    status: string;
}

export interface DeletePublishedRequest {
    id: number;
    wp_url: string;
    wp_user: string;
    wp_password: string;
}

export interface UpdateArticleRequest {
    content: string;
}

export interface Job {
    job_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    topic: string;
    result?: string;
    error?: string;
    created_at: string;
    completed_at?: string;
}

export interface Article {
    filename: string;
    size: number;
    created: string;
    modified: string;
}

export interface AgentSettings {
    provider: string;
    model: string;
}

export interface AgentsConfig {
    agents: Record<string, AgentSettings>;
}

export interface RunSniperRequest {
    query?: string;
    min_profit: number;
    auto: boolean;
    discover: boolean;
    mock: boolean;
}

export const api = {
    // Sniper Endpoints
    runSniper: (data: RunSniperRequest) => axios.post<{ status: string, message: string }>(`${API_BASE}/sniper/run`, data),
    getSniperStatus: () => axios.get<any>(`${API_BASE}/sniper/status`),
    getSniperResults: () => axios.get<any>(`${API_BASE}/sniper/results`),
    getRateLimitStatus: () => axios.get<any>(`${API_BASE}/sniper/rate-limit`),
    
    // Legacy / Shared
    getLogs: (lines: number = 100) => axios.get<{ logs: string[] }>(`${API_BASE}/logs?lines=${lines}`),
    getAgentConfig: () => axios.get<AgentsConfig>(`${API_BASE}/config/agents`),
    updateAgentConfig: (config: AgentsConfig) => axios.post<AgentsConfig>(`${API_BASE}/config/agents`, config)
};
