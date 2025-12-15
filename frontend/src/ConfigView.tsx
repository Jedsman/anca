import { useState, useEffect } from 'react';
import { api } from './api';
import type { AgentsConfig } from './api';
import { Settings, Save, Loader2, RefreshCw } from 'lucide-react';
import { Button } from './components/ui/button'; // Assuming we have this or similar styles

export default function ConfigView() {
    const [config, setConfig] = useState<AgentsConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        setLoading(true);
        try {
            const res = await api.getAgentConfig();
            setConfig(res.data);
        } catch (err) {
            console.error("Failed to load config", err);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!config) return;
        setSaving(true);
        try {
            await api.updateAgentConfig(config);
        } catch (err) {
            alert("Failed to save config: " + err);
        } finally {
            setSaving(false);
        }
    };

    const handleUpdateAgent = (agent: string, field: 'provider' | 'model', value: string) => {
        if (!config) return;
        setConfig({
            ...config,
            agents: {
                ...config.agents,
                [agent]: {
                    ...config.agents[agent],
                    [field]: value
                }
            }
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-zinc-500 gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Loading Configuration...
            </div>
        );
    }

    if (!config) return <div>Error loading configuration.</div>;

    const agents = Object.keys(config.agents).sort();

    return (
        <div className="flex flex-col gap-6 max-w-4xl mx-auto p-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Settings className="w-6 h-6 text-purple-400" />
                    <div>
                        <h2 className="text-xl font-semibold text-zinc-100">Agent Configuration</h2>
                        <p className="text-sm text-zinc-400">Configure LLM providers and models per agent.</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button onClick={loadConfig} className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-400 transition-colors">
                        <RefreshCw className="w-4 h-4" />
                    </button>
                    <Button onClick={handleSave} loading={saving} className="bg-purple-600 hover:bg-purple-700 text-white border-none">
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                    </Button>
                </div>
            </div>

            <div className="bg-[#1e1e1e] border border-zinc-800 rounded-xl overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-zinc-900 border-b border-zinc-800">
                        <tr>
                            <th className="p-4 text-xs font-medium text-zinc-500 uppercase w-1/4">Agent Name</th>
                            <th className="p-4 text-xs font-medium text-zinc-500 uppercase w-1/4">Provider</th>
                            <th className="p-4 text-xs font-medium text-zinc-500 uppercase w-1/2">Model Identification</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                        {agents.map(agent => (
                            <tr key={agent} className="group hover:bg-zinc-800/30 transition-colors">
                                <td className="p-4 font-mono text-sm text-zinc-300 font-medium capitalize">
                                    {agent.replace('_', ' ')}
                                </td>
                                <td className="p-4">
                                     <select 
                                        className="bg-black/20 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-200 focus:border-purple-500 focus:outline-none w-full appearance-none"
                                        value={config.agents[agent].provider}
                                        onChange={e => handleUpdateAgent(agent, 'provider', e.target.value)}
                                    >
                                        <option value="gemini">Gemini</option>
                                        <option value="ollama">Ollama</option>
                                        <option value="groq">Groq</option>
                                        <option value="openai">OpenAI</option>
                                        <option value="anthropic">Anthropic</option>
                                    </select>
                                </td>
                                <td className="p-4">
                                    <input 
                                        type="text" 
                                        className="bg-black/20 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-200 focus:border-purple-500 focus:outline-none w-full"
                                        value={config.agents[agent].model}
                                        onChange={e => handleUpdateAgent(agent, 'model', e.target.value)}
                                        placeholder="e.g. gemini-1.5-flash"
                                    />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            <div className="bg-blue-900/10 border border-blue-800/30 p-4 rounded-xl text-sm text-blue-200">
                <strong>Note:</strong> The 'Default' agent settings are used as a fallback for any agent not explicitly configured or if per-agent settings are missing.
            </div>
        </div>
    );
}
