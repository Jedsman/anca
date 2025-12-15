import { useState, useEffect } from 'react';
import { 
  Terminal, LayoutDashboard, FileText, Settings, 
  Sparkles, CheckCircle2, AlertCircle, Loader2,
  Globe, ShoppingCart, Send, Activity, Trash2, Edit2, Save
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from './api';
import type { Job, Article, GenerateRequest } from './api';
import ConfigView from './ConfigView';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

// --- Constants ---
const PROVIDERS = [
    { value: 'gemini', label: 'Google Gemini' },
    { value: 'ollama', label: 'Ollama (Local)' },
    { value: 'groq', label: 'Groq (Fast)' }
];

const MODELS: Record<string, { value: string, label: string }[]> = {
    gemini: [
        { value: 'gemini-1.5-flash-latest', label: 'Gemini 1.5 Flash' },
        { value: 'gemini-1.5-pro-latest', label: 'Gemini 1.5 Pro' },
        { value: 'gemini-1.5-flash-8b-latest', label: 'Gemini 1.5 Flash 8B' }
    ],
    ollama: [
        { value: 'mistral:7b', label: 'Mistral 7B' },
        { value: 'llama3.1:8b', label: 'Llama 3.1 8B' },
        { value: 'qwen2.5:7b-instruct', label: 'Qwen 2.5 7B' },
        { value: 'gemma:7b', label: 'Gemma 7B' }
    ],
    groq: [
        { value: 'llama-3.1-8b-instant', label: 'Llama 3 8B' },
        { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B' }
    ]
};

import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Select } from './components/ui/select';
import { StatusBadge } from './components/ui/status-badge';

// ... Constants ...

// --- Views ---

function GeneratorView({ onNavigate }: { onNavigate: (view: 'create' | 'library' | 'logs') => void }) {
    const [loading, setLoading] = useState(false);
    const [jobs, setJobs] = useState<Job[]>([]);
    // Discovery State
    const [discoveryLoading, setDiscoveryLoading] = useState(false);
    const [showDiscovery, setShowDiscovery] = useState(false);
    const [discoveredTopics, setDiscoveredTopics] = useState<string[]>([]);
    const [selectedDiscoveredTopic, setSelectedDiscoveredTopic] = useState('');

    const [formData, setFormData] = useState<GenerateRequest>({
        topic: '',
        affiliate: false,
        niche: '',
        discover_mode: false,
        provider: 'gemini',
        model: 'gemini-1.5-flash-latest'
    });

    useEffect(() => {
        refreshJobs();
        const interval = setInterval(refreshJobs, 5000);
        return () => clearInterval(interval);
    }, []);

    const refreshJobs = () => {
        api.listJobs().then(res => setJobs(res.data.reverse())).catch(console.error);
    };

    const handleDiscovery = async () => {
        setDiscoveryLoading(true);
        try {
            const res = await api.discoverTopics({
                niche: formData.niche || undefined,
                affiliate: formData.affiliate,
                provider: formData.provider,
                model: formData.model
            });
            setDiscoveredTopics(res.data.topics);
            setShowDiscovery(true);
        } catch (err) {
            alert("Discovery failed: " + err);
        } finally {
            setDiscoveryLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        // If interactive discovery mode is on and we haven't picked a topic yet
        if (formData.discover_mode && !showDiscovery && !formData.only_discovery) {
            // "Find Trends" step
            handleDiscovery();
            return;
        }

        // Standard generation or "Research Only" or "Generate Selected"
        setLoading(true);
        try {
            await api.generate({
                ...formData,
                niche: formData.niche || undefined 
            });
            
            // Reset UI after launch
            refreshJobs();
            setFormData(prev => ({ ...prev, topic: '' })); 
            setShowDiscovery(false);
            setDiscoveredTopics([]);
            setSelectedDiscoveredTopic('');
            
        } catch (err) {
            alert("Failed to start job: " + err);
        } finally {
            setLoading(false);
        }
    };

    // If showing discovery results
    if (showDiscovery) {
        return (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
                <div className="lg:col-span-2 flex flex-col gap-6 h-full">
                    <div className="bg-zinc-800/50 backdrop-blur border border-zinc-700/50 p-6 rounded-xl flex flex-col h-full">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-500">
                                    <Sparkles className="w-5 h-5" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold text-white">Discovered Trends</h2>
                                    <p className="text-sm text-zinc-400">Select a topic to generate content for</p>
                                </div>
                            </div>
                            <button 
                                onClick={() => setShowDiscovery(false)}
                                className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
                            >
                                Back to Criteria
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                            {discoveredTopics.map((topic, idx) => (
                                <label 
                                    key={idx} 
                                    className={clsx(
                                        "block p-4 rounded-xl border cursor-pointer transition-all",
                                        selectedDiscoveredTopic === topic 
                                            ? "bg-blue-600/10 border-blue-500 shadow-sm shadow-blue-500/10" 
                                            : "bg-zinc-900/30 border-zinc-800 hover:bg-zinc-800/50 hover:border-zinc-700"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <input 
                                            type="radio" 
                                            name="topic_selection"
                                            className="mt-1 w-4 h-4 text-blue-500 bg-zinc-800 border-zinc-600 focus:ring-blue-500 focus:ring-offset-zinc-900"
                                            value={topic}
                                            checked={selectedDiscoveredTopic === topic}
                                            onChange={() => {
                                                setSelectedDiscoveredTopic(topic);
                                                setFormData(prev => ({ ...prev, topic: topic }));
                                                // Turn off discover_mode flag so backend generates directly
                                                setFormData(prev => ({ ...prev, topic: topic, discover_mode: false }));
                                            }}
                                        />
                                        <span className={clsx("text-sm transition-colors", selectedDiscoveredTopic === topic ? "text-blue-100 font-medium" : "text-zinc-300")}>
                                            {topic}
                                        </span>
                                    </div>
                                </label>
                            ))}
                        </div>

                        <div className="mt-6 pt-6 border-t border-zinc-700/50 flex justify-end gap-3">
                            <Button 
                                variant="secondary"
                                onClick={() => setShowDiscovery(false)}
                            >
                                Cancel
                            </Button>
                            <Button 
                                onClick={handleSubmit}
                                disabled={!selectedDiscoveredTopic || loading}
                                loading={loading}
                            >
                                Generate Selected Topic
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Sidebar Context */}
                <div className="lg:col-span-1">
                     <div className="bg-zinc-800/30 border border-zinc-700/50 p-6 rounded-xl">
                        <h3 className="font-medium text-zinc-200 mb-2">Search Context</h3>
                        <div className="space-y-4 text-sm text-zinc-400">
                            <div>
                                <span className="block text-xs uppercase tracking-wider text-zinc-600 mb-1">Niche</span>
                                <span className="text-zinc-300">{formData.niche || "General"}</span>
                            </div>
                            <div>
                                <span className="block text-xs uppercase tracking-wider text-zinc-600 mb-1">Mode</span>
                                <span className="text-zinc-300">{formData.affiliate ? "Affiliate Buyer's Guide" : "Informational"}</span>
                            </div>
                             <div>
                                <span className="block text-xs uppercase tracking-wider text-zinc-600 mb-1">Model</span>
                                <span className="text-zinc-300">{formData.model}</span>
                            </div>
                        </div>
                     </div>
                </div>
            </div>
        );
    }


    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            {/* Form */}
            <div className="lg:col-span-1 flex flex-col gap-6">
                <div className="bg-zinc-800/50 backdrop-blur border border-zinc-700/50 p-6 rounded-xl">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
                            <Sparkles className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Generator</h2>
                            <p className="text-sm text-zinc-400">Launch a new content workflow</p>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                        <Input 
                            label="Topic" 
                            placeholder="e.g. Best Coffee Makers 2025" 
                            value={formData.topic}
                            onChange={(e: any) => setFormData({...formData, topic: e.target.value})}
                            required
                        />
                        
                        <div className="grid grid-cols-2 gap-4">
                            <Select 
                                label="Mode"
                                options={[
                                    { value: 'Standard', label: 'Standard Blog' },
                                    { value: 'Discovery', label: 'Discovery (Find Trend)' }
                                ]}
                                onChange={(e: any) => {
                                    const isDisco = e.target.value === 'Discovery';
                                    setFormData({
                                        ...formData, 
                                        discover_mode: isDisco,
                                        topic: isDisco ? 'Auto-Discovery' : '' 
                                    });
                                }}
                            />
                             <Select 
                                label="Type"
                                options={[
                                    { value: 'Info', label: 'Informational' },
                                    { value: 'Affiliate', label: 'Buyer\'s Guide (Affiliate)' }
                                ]}
                                onChange={(e: any) => setFormData({...formData, affiliate: e.target.value === 'Affiliate'})}
                            />
                        </div>



                        {/* Model Configuration */}
                        <div className="bg-zinc-900/50 p-3 rounded-lg border border-zinc-800 flex flex-col gap-3">
                             <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-zinc-500 uppercase">AI Configuration</span>
                                <Settings className="w-3 h-3 text-zinc-600" />
                             </div>
                             
                             <div className="grid grid-cols-2 gap-3">
                                <Select 
                                    label="Provider"
                                    options={PROVIDERS}
                                    value={formData.provider}
                                    onChange={(e: any) => {
                                        const newProvider = e.target.value;
                                        setFormData({
                                            ...formData, 
                                            provider: newProvider,
                                            model: MODELS[newProvider]?.[0]?.value || '' 
                                        });
                                    }}
                                />
                                <Select 
                                    label="Model" 
                                    options={MODELS[formData.provider || 'gemini'] || []}
                                    value={formData.model}
                                    onChange={(e: any) => setFormData({...formData, model: e.target.value})}
                                />
                             </div>
                        </div>

                        {formData.discover_mode ? (
                             <div className="space-y-3">
                                <Input 
                                    label="Target Niche (Optional)" 
                                    placeholder="e.g. Sustainable Tech" 
                                    value={formData.niche}
                                    onChange={(e: any) => setFormData({...formData, niche: e.target.value})}
                                />
                                {/* Only Discovery Option (Research Mode) */}
                                <label className="flex items-center gap-2 p-3 bg-zinc-900/50 rounded-lg border border-zinc-800 cursor-pointer hover:border-zinc-700 transition-colors">
                                    <input 
                                        type="checkbox" 
                                        className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-zinc-900"
                                        checked={formData.only_discovery || false} // Provide default
                                        onChange={(e: any) => setFormData({...formData, only_discovery: e.target.checked})}
                                    />
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-zinc-300">Research Only</span>
                                        <span className="text-xs text-zinc-500">Find trend but don't write article</span>
                                    </div>
                                </label>
                             </div>
                        ) : (
                             <Input 
                                label="Topic" 
                                placeholder="e.g. Best Coffee Makers 2025" 
                                value={formData.topic}
                                onChange={(e: any) => setFormData({...formData, topic: e.target.value})}
                                required
                            />
                        )}

                        <div className="h-px bg-zinc-700/50 my-2" />
                        
                        <div className="flex gap-2 text-xs text-zinc-500">
                             <span className="flex items-center gap-1"><Globe className="w-3 h-3" /> Web Search</span>
                             <span className="flex items-center gap-1"><ShoppingCart className="w-3 h-3" /> Affiliate Data</span>
                        </div>

                        <Button type="submit" loading={loading || discoveryLoading} className="w-full mt-2">
                            {formData.discover_mode && !formData.only_discovery ? (
                                <span className="flex items-center justify-center gap-2">
                                    <Sparkles className="w-4 h-4" /> Find Trends
                                </span>
                            ) : "Start Generation"}
                        </Button>
                    </form>
                </div>
            </div>

            {/* Live Jobs */}
            <div className="lg:col-span-2 flex flex-col gap-4 overflow-hidden">
                <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Active Jobs</h3>
                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                    {jobs.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-40 text-zinc-500 border border-dashed border-zinc-700 rounded-xl">
                            <Terminal className="w-8 h-8 mb-2 opacity-50" />
                            <p>No jobs running</p>
                        </div>
                    )}
                    {jobs.map(job => (
                        <div key={job.job_id} className="bg-zinc-800/30 border border-zinc-700/50 p-4 rounded-xl flex items-center justify-between hover:border-zinc-600 transition-colors group">
                            <div className="flex items-center gap-4">
                                <div className={clsx("w-2 h-2 rounded-full", job.status === 'running' ? 'bg-blue-500 animate-pulse' : 'bg-zinc-600')} />
                                <div>
                                    <h4 className="font-medium text-zinc-200">{job.topic}</h4>
                                    <p className="text-xs text-zinc-500 font-mono">{job.job_id.slice(0, 8)} • {new Date(job.created_at).toLocaleTimeString()}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <StatusBadge status={job.status} />
                                <button 
                                    onClick={() => onNavigate('logs')}
                                    className="p-1.5 rounded-lg text-zinc-500 hover:text-blue-400 hover:bg-zinc-700 transition-colors opacity-0 group-hover:opacity-100"
                                    title="View System Logs"
                                >
                                    <Activity className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function ArticlesView({ onEdit }: { onEdit: (filename: string) => void }) {
    const [articles, setArticles] = useState<Article[]>([]);
    const [publishing, setPublishing] = useState<string | null>(null);

    // Published Creds State (Simplified)
    const [wpConfig, setWpConfig] = useState({
        url: 'http://anca.local',
        user: 'jedsman',
        password: '' // Don't allow empty, user must enter
    });

    useEffect(() => {
        loadArticles();
    }, []);

    const loadArticles = () => api.listArticles().then(res => setArticles(res.data.articles)).catch(console.error);

    // Map filename -> published details
    const [publishedLinks, setPublishedLinks] = useState<Record<string, string>>({});
    const [publishedIds, setPublishedIds] = useState<Record<string, number>>({});

    const handlePublish = async (filename: string) => {
        if (!wpConfig.password) {
            alert("Please enter WordPress Application Password!");
            return;
        }
        setPublishing(filename);
        try {
            const res = await api.publishArticle({
                filename,
                wp_url: wpConfig.url,
                wp_user: wpConfig.user,
                wp_password: wpConfig.password,
                status: 'publish'
            });
            
            const link = (res.data as any).link;
            const id = (res.data as any).id;
            
            if (link) setPublishedLinks(prev => ({ ...prev, [filename]: link }));
            if (id) setPublishedIds(prev => ({ ...prev, [filename]: id }));

            if (link) {
                const openIdx = window.confirm("Published Successfully! Open link now?\n" + link);
                if (openIdx) window.open(link, '_blank');
            } else {
                alert("Published Successfully (No link returned)");
            }

        } catch (err) {
            alert("Publish Failed: " + err);
        } finally {
            setPublishing(null);
        }
    };

    const handleDeleteLocal = async (filename: string) => {
        if (!window.confirm("Delete this article locally? This cannot be undone.")) return;
        try {
            await api.deleteArticle(filename);
            loadArticles(); // Refresh list
        } catch (err) {
            alert("Delete failed: " + err);
        }
    };

    const handleDeleteRemote = async (filename: string) => {
        const id = publishedIds[filename];
        if (!id) return;
        
        if (!window.confirm("Delete this article from WordPress? This cannot be undone.")) return;
        try {
            await api.deletePublished({
                id,
                wp_url: wpConfig.url,
                wp_user: wpConfig.user,
                wp_password: wpConfig.password
            });
            
            // Clear state
            setPublishedIds(prev => { const n = {...prev}; delete n[filename]; return n; });
            setPublishedLinks(prev => { const n = {...prev}; delete n[filename]; return n; });
            alert("Deleted from WordPress!");
            
        } catch (err) {
            alert("Remote delete failed: " + err);
        }
    };

    return (
        <div className="flex flex-col gap-6 h-full">
            {/* Header / Config Bar */}
            <div className="bg-zinc-800/50 border border-zinc-700/50 p-4 rounded-xl flex items-center gap-4">
                <div className="flex items-center gap-2 text-zinc-400">
                    <Settings className="w-4 h-4" />
                    <span className="text-sm font-medium">Publisher Config</span>
                </div>
                <div className="w-px h-6 bg-zinc-700" />
                <div className="flex gap-4 flex-1">
                    <input className="bg-transparent border-b border-zinc-700 focus:border-blue-500 outline-none text-sm px-2 py-1 text-zinc-300 w-48" 
                        value={wpConfig.url} onChange={e => setWpConfig({...wpConfig, url: e.target.value})} placeholder="WP URL" />
                    <input className="bg-transparent border-b border-zinc-700 focus:border-blue-500 outline-none text-sm px-2 py-1 text-zinc-300 w-32" 
                        value={wpConfig.user} onChange={e => setWpConfig({...wpConfig, user: e.target.value})} placeholder="User" />
                    <input className="bg-transparent border-b border-zinc-700 focus:border-blue-500 outline-none text-sm px-2 py-1 text-zinc-300 w-64" 
                        type="password" value={wpConfig.password} onChange={e => setWpConfig({...wpConfig, password: e.target.value})} placeholder="App Password" />
                </div>
            </div>

            {/* List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto pb-10">
                {articles.map(article => (
                     <div key={article.filename} className="bg-[#1e1e1e] border border-zinc-800 hover:border-zinc-600 p-5 rounded-xl flex flex-col justify-between gap-4 transition-all group">
                        <div>
                            <div className="flex items-start justify-between mb-2">
                                <div className="p-2 bg-zinc-800 rounded-lg text-zinc-400 group-hover:text-blue-400 transition-colors">
                                    <FileText className="w-5 h-5" />
                                </div>
                                <span className="text-xs text-zinc-600 font-mono">{(article.size / 1024).toFixed(1)} KB</span>
                            </div>
                            <h3 className="font-medium text-zinc-200 line-clamp-2 leading-snug" title={article.filename}>
                                {article.filename.replace(/_/g, ' ').replace('.md', '')}
                            </h3>
                            <p className="text-xs text-zinc-500 mt-2">
                                {new Date(article.modified).toLocaleDateString()}
                            </p>
                        </div>
                        
                        <div className="flex gap-2 mb-3 justify-end">
                             {/* Edit Button */}
                             <button 
                                onClick={() => onEdit(article.filename)}
                                className="p-1.5 rounded-lg text-zinc-500 hover:text-blue-400 hover:bg-zinc-800 transition-colors"
                                title="Edit Article"
                            >
                                <Edit2 className="w-4 h-4" />
                            </button>

                             {/* Delete Remote (Only if published in this session) */}
                             {publishedIds[article.filename] && (
                                <button 
                                    onClick={() => handleDeleteRemote(article.filename)}
                                    className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-zinc-800 transition-colors"
                                    title="Delete from WordPress"
                                >
                                    <Globe className="w-4 h-4" />
                                    <Trash2 className="w-3 h-3 absolute ml-2.5 -mt-1" />
                                </button>
                             )}
                             
                             {/* Delete Local */}
                             <button 
                                onClick={() => handleDeleteLocal(article.filename)}
                                className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-zinc-800 transition-colors"
                                title="Delete File"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                        
                        <div className="flex gap-2">
                             {publishedLinks[article.filename] ? (
                                <Button 
                                    variant="outline" 
                                    className="w-full text-xs h-8 text-green-400 border-green-500/30 hover:bg-green-500/10" 
                                    onClick={() => window.open(publishedLinks[article.filename], '_blank')}
                                >
                                    <Globe className="w-3 h-3" />
                                    View Post
                                </Button>
                             ) : (
                                <Button 
                                    variant="secondary" 
                                    className="w-full text-xs h-8" 
                                    onClick={() => handlePublish(article.filename)}
                                    loading={publishing === article.filename}
                                >
                                    <Send className="w-3 h-3" />
                                    Publish to WP
                                </Button>
                             )}
                        </div>
                     </div>
                ))}
            </div>
        </div>
    );
}

function LogsView() {
    const [logs, setLogs] = useState<string[]>([]);
    const [autoRefresh, setAutoRefresh] = useState(true);

    useEffect(() => {
        loadLogs();
        const interval = setInterval(() => {
            if (autoRefresh) loadLogs();
        }, 2000);
        return () => clearInterval(interval);
    }, [autoRefresh]);

    const loadLogs = () => api.getLogs().then(res => setLogs(res.data.logs)).catch(console.error);

    return (
        <div className="flex flex-col gap-4 h-full">
            <div className="flex items-center justify-between bg-zinc-800/50 p-4 rounded-xl border border-zinc-700/50">
                <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-blue-400" />
                    <h3 className="font-medium text-zinc-200">System Logs</h3>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-xs text-zinc-500 font-mono">
                        {logs.length > 0 ? 'Live Stream' : 'Connecting...'}
                    </span>
                    <button 
                        onClick={() => setAutoRefresh(!autoRefresh)}
                        className={clsx("px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors", 
                            autoRefresh ? "bg-green-500/10 text-green-500 border-green-500/20" : "bg-zinc-800 text-zinc-400 border-zinc-700 hover:text-zinc-200")}
                    >
                        {autoRefresh ? "Auto-Refresh ON" : "Paused"}
                    </button>
                </div>
            </div>

            <div className="flex-1 bg-[#0a0a0a] border border-zinc-800 rounded-xl p-4 overflow-y-auto font-mono text-xs leading-relaxed text-zinc-400 shadow-inner">
                {logs.map((line, i) => (
                    <div key={i} className="hover:bg-white/5 px-2 py-0.5 rounded border-l-2 border-transparent hover:border-blue-500/50 transition-all">
                        <span className="opacity-50 select-none mr-3">{i+1}</span>
                        {line}
                    </div>
                ))}
                <div id="log-end" />
            </div>
        </div>
    );
}

function EditorView({ filename, onClose }: { filename: string, onClose: () => void }) {
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadContent();
    }, [filename]);

    const loadContent = async () => {
        setLoading(true);
        try {
            const res = await api.getArticle(filename);
            setContent(res.data); // data is text
        } catch (err) {
            alert("Failed to load article: " + err);
            onClose();
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await api.updateArticle(filename, content);
            // alert("Saved!"); // Optional feedback, maybe too intrusive
        } catch (err) {
            alert("Save failed: " + err);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-zinc-500 gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Loading Editor...
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full gap-4">
            <div className="flex items-center justify-between bg-zinc-800/50 p-4 rounded-xl border border-zinc-700/50">
                <div className="flex items-center gap-3">
                    <Edit2 className="w-5 h-5 text-blue-400" />
                    <div>
                        <h3 className="font-medium text-zinc-200">Editor</h3>
                        <p className="text-xs text-zinc-500 font-mono">{filename}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                     <Button variant="secondary" onClick={onClose}>
                        Close
                     </Button>
                     <Button onClick={handleSave} loading={saving}>
                        <Save className="w-4 h-4" />
                        Save Changes
                     </Button>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
                {/* Editor Pane */}
                <div className="flex flex-col gap-2">
                    <span className="text-xs font-medium text-zinc-500 uppercase">Markdown Source</span>
                    <textarea 
                        className="flex-1 bg-[#1e1e1e] border border-zinc-800 rounded-xl p-4 font-mono text-sm text-zinc-300 focus:outline-none focus:border-blue-500/50 resize-none leading-relaxed"
                        value={content}
                        onChange={e => setContent(e.target.value)}
                        placeholder="# Start writing..."
                    />
                </div>

                {/* Preview Pane */}
                <div className="flex flex-col gap-2">
                    <span className="text-xs font-medium text-zinc-500 uppercase">Live Preview</span>
                    <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl p-8 overflow-y-auto prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                </div>
            </div>
        </div>
    );
}

// --- Main App ---

export default function App() {
  const [view, setView] = useState<'create' | 'library' | 'logs' | 'editor' | 'config'>('create');
  const [editingFilename, setEditingFilename] = useState<string>(''); // Track which file is being edited

  const handleEdit = (filename: string) => {
      setEditingFilename(filename);
      setView('editor');
  };

  const handleEditorClose = () => {
      setEditingFilename('');
      setView('library');
  };

  console.log("App component rendering...");
  return (
    <div className="flex h-screen bg-[#111111] text-zinc-100 font-sans selection:bg-blue-500/30">
      {/* Sidebar */}
      <div className="w-64 border-r border-zinc-800 bg-[#161616] flex flex-col">
        <div className="p-6">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                ANCA
            </h1>
            <p className="text-xs text-zinc-500 mt-1">Agentic Neural Coding Assistant</p>
        </div>

        <nav className="flex-1 px-4 space-y-1">
            <button 
                onClick={() => setView('create')}
                className={clsx("w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all", 
                view === 'create' ? "bg-blue-600/10 text-blue-400" : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200")}
            >
                <LayoutDashboard className="w-4 h-4" />
                Generator
            </button>
            <button 
                onClick={() => setView('library')}
                className={clsx("w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all", 
                view === 'library' || view === 'editor' ? "bg-blue-600/10 text-blue-400" : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200")}
            >
                <FileText className="w-4 h-4" />
                Library
            </button>
            <button 
                onClick={() => setView('logs')}
                className={clsx("w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all", 
                view === 'logs' ? "bg-blue-600/10 text-blue-400" : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200")}
            >
                <Activity className="w-4 h-4" />
                System Logs
            </button>
            <button 
                onClick={() => setView('config')}
                className={clsx("w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all", 
                view === 'config' ? "bg-blue-600/10 text-blue-400" : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200")}
            >
                <Settings className="w-4 h-4" />
                Settings
            </button>
        </nav>

        <div className="p-4 border-t border-zinc-800">
            <div className="flex items-center gap-3 px-4 py-2 text-xs text-zinc-500">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                System Online
            </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-hidden h-full">
         <div className="max-w-6xl mx-auto h-full flex flex-col">
            <header className="mb-8 flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">
                        {view === 'create' ? 'Dashboard' : view === 'library' ? 'Article Library' : view === 'editor' ? 'Content Editor' : view === 'config' ? 'Configuration' : 'System Logs'}
                    </h2>
                    <p className="text-sm text-zinc-400 mt-1">
                         {view === 'create' ? 'Manage your content generation pipeline' : view === 'library' ? 'View and publish your generated content' : view === 'editor' ? 'Edit markdown content with live preview' : view === 'config' ? 'Manage system and agent settings' : 'Real-time application activity'}
                    </p>
                </div>
            </header>

            <div className="flex-1 min-h-0">
                {view === 'create' ? (
                    <GeneratorView onNavigate={setView} />
                ) : view === 'library' ? (
                    <ArticlesView onEdit={handleEdit} /> 
                ) : view === 'editor' ? (
                    <EditorView filename={editingFilename} onClose={handleEditorClose} />
                ) : view === 'config' ? (
                    <ConfigView />
                ) : (
                    <LogsView />
                )}
            </div>
         </div>
      </main>
    </div>
  );
}
