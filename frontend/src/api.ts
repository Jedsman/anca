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

export const api = {
    generate: (data: GenerateRequest) => axios.post<Job>(`${API_BASE}/generate`, data),
    getJob: (jobId: string) => axios.get<Job>(`${API_BASE}/status/${jobId}`),
    listJobs: () => axios.get<Job[]>(`${API_BASE}/jobs`),
    listArticles: () => axios.get<{ articles: Article[] }>(`${API_BASE}/articles`),
    deleteArticle: (filename: string) => axios.delete(`${API_BASE}/articles/${filename}`),
    publishArticle: (data: PublishRequest) => axios.post(`${API_BASE}/publish`, data),
    deletePublished: (data: DeletePublishedRequest) => axios.post(`${API_BASE}/publish/delete`, data),
    updateArticle: (filename: string, content: string) => axios.put(`${API_BASE}/articles/${filename}`, { content }),
    getArticle: (filename: string) => axios.get(`${API_BASE}/articles/${filename}`, { responseType: 'text' }),
    getLogs: (lines: number = 100) => axios.get<{ logs: string[] }>(`${API_BASE}/logs?lines=${lines}`),
    discoverTopics: (data: DiscoverRequest) => axios.post<{ topics: string[], count: number }>(`${API_BASE}/discover_topics`, data),
    getAgentConfig: () => axios.get<AgentsConfig>(`${API_BASE}/config/agents`),
    updateAgentConfig: (config: AgentsConfig) => axios.post<AgentsConfig>(`${API_BASE}/config/agents`, config)
};
