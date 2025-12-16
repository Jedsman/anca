import { useState, useEffect } from 'react';
import { Terminal, Activity, Play, Target, TrendingUp, DollarSign, ExternalLink, Sparkles } from 'lucide-react';
import { api } from './api';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { StatusBadge } from './components/ui/status-badge';

export default function SniperView() {
    const [status, setStatus] = useState<any>(null);
    const [rateLimit, setRateLimit] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [query, setQuery] = useState('');
    const [minProfit, setMinProfit] = useState(10.0);
    const [mode, setMode] = useState<'discover' | 'niche' | 'search'>('discover');
    const [mock, setMock] = useState(false);

    useEffect(() => {
        refreshStatus();
        const interval = setInterval(refreshStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    const refreshStatus = () => {
        api.getSniperStatus().then(res => setStatus(res.data)).catch(console.error);
        api.getRateLimitStatus().then(res => setRateLimit(res.data)).catch(console.error);
    };

    const handleRun = async () => {
        setLoading(true);
        try {
            await api.runSniper({
                query: query || undefined,
                min_profit: minProfit,
                auto: mode === 'niche',
                discover: mode === 'discover',
                mock: mock
            });
            refreshStatus();
        } catch (err: any) {
            alert("Failed to start sniper: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const isRunning = status?.status === 'running';
    const dealCount = status?.result?.deals?.length || 0;
    const totalProfit = status?.result?.deals?.reduce((sum: number, d: any) => sum + (d.analysis?.profit || 0), 0) || 0;

    return (
        <div className="flex flex-col gap-6 h-full">
            {/* Stats Banner */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="group bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 backdrop-blur-sm p-5 rounded-2xl border border-emerald-500/20 hover:border-emerald-500/40 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/10">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs text-emerald-400/80 font-medium uppercase tracking-wider mb-1">Deals Found</p>
                            <p className="text-3xl font-bold text-white">{dealCount}</p>
                        </div>
                        <div className="p-3 bg-emerald-500/20 rounded-xl group-hover:scale-110 transition-transform">
                            <Target className="w-6 h-6 text-emerald-400" />
                        </div>
                    </div>
                </div>

                <div className="group bg-gradient-to-br from-blue-500/10 to-blue-600/5 backdrop-blur-sm p-5 rounded-2xl border border-blue-500/20 hover:border-blue-500/40 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs text-blue-400/80 font-medium uppercase tracking-wider mb-1">Total Profit</p>
                            <p className="text-3xl font-bold text-white">£{totalProfit.toFixed(2)}</p>
                        </div>
                        <div className="p-3 bg-blue-500/20 rounded-xl group-hover:scale-110 transition-transform">
                            <TrendingUp className="w-6 h-6 text-blue-400" />
                        </div>
                    </div>
                </div>

                <div className="group bg-gradient-to-br from-purple-500/10 to-purple-600/5 backdrop-blur-sm p-5 rounded-2xl border border-purple-500/20 hover:border-purple-500/40 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs text-purple-400/80 font-medium uppercase tracking-wider mb-1">API Calls</p>
                            <p className="text-3xl font-bold text-white">{rateLimit?.calls_today || 0}</p>
                            <p className="text-xs text-purple-400/60 mt-1">/ {rateLimit?.max_calls_per_day || 5000}</p>
                        </div>
                        <div className="p-3 bg-purple-500/20 rounded-xl group-hover:scale-110 transition-transform">
                            <Activity className="w-6 h-6 text-purple-400" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Control Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1 bg-gradient-to-br from-zinc-900/90 to-zinc-800/90 backdrop-blur-xl p-6 rounded-2xl border border-zinc-700/50 shadow-2xl">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="relative">
                            <div className="absolute inset-0 bg-gradient-to-br from-emerald-400 to-blue-500 rounded-xl blur-md opacity-50"></div>
                            <div className="relative w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-blue-600 flex items-center justify-center shadow-lg">
                                <Sparkles className="w-6 h-6 text-white" />
                            </div>
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Agent Control</h2>
                            <p className="text-xs text-zinc-400">Configure & launch sniper</p>
                        </div>
                    </div>

                    {/* Rate Limit Progress */}
                    {rateLimit && (
                        <div className="bg-black/30 p-4 rounded-xl border border-zinc-700/30 mb-6">
                            <div className="flex justify-between text-xs text-zinc-400 mb-2">
                                <span className="font-medium">API Quota Usage</span>
                                <span className="text-zinc-300">{((rateLimit.calls_today / rateLimit.max_calls_per_day) * 100).toFixed(1)}%</span>
                            </div>
                            <div className="relative w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                                <div
                                    className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ${
                                        rateLimit.calls_today > 4000
                                            ? 'bg-gradient-to-r from-red-500 to-orange-500'
                                            : 'bg-gradient-to-r from-emerald-500 to-blue-500'
                                    }`}
                                    style={{ width: `${Math.min(100, (rateLimit.calls_today / rateLimit.max_calls_per_day) * 100)}%` }}
                                />
                            </div>
                            <p className="text-xs text-zinc-500 mt-2">
                                {rateLimit.remaining_calls.toLocaleString()} calls remaining today
                            </p>
                        </div>
                    )}

                    <div className="space-y-5">
                        {/* Mode Selection */}
                        <div>
                            <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wider">Sniper Mode</label>
                            <div className="grid grid-cols-3 gap-2 bg-black/30 p-1 rounded-xl border border-zinc-800/50">
                                <button
                                    onClick={() => setMode('discover')}
                                    className={`px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                                        mode === 'discover'
                                            ? 'bg-gradient-to-br from-emerald-500 to-blue-500 text-white shadow-lg shadow-emerald-500/20'
                                            : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                                    }`}
                                >
                                    Discovery
                                </button>
                                <button
                                    onClick={() => setMode('niche')}
                                    className={`px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                                        mode === 'niche'
                                            ? 'bg-gradient-to-br from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/20'
                                            : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                                    }`}
                                >
                                    Niche
                                </button>
                                <button
                                    onClick={() => setMode('search')}
                                    className={`px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                                        mode === 'search'
                                            ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/20'
                                            : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                                    }`}
                                >
                                    Search
                                </button>
                            </div>
                        </div>

                        {mode !== 'discover' && (
                            <Input
                                label={mode === 'niche' ? "Niche Name" : "Search Query"}
                                value={query}
                                onChange={(e: any) => setQuery(e.target.value)}
                                placeholder={mode === 'niche' ? "e.g. Vintage Cameras" : "e.g. Sony Walkman WM-2"}
                            />
                        )}

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wider">Min Profit (£)</label>
                                <input
                                    type="number"
                                    value={minProfit}
                                    onChange={(e) => setMinProfit(parseFloat(e.target.value))}
                                    className="w-full bg-black/30 border border-zinc-700/50 rounded-xl px-4 py-2.5 text-sm focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 outline-none transition-all"
                                />
                            </div>
                            <div className="flex items-end">
                                <label className="flex items-center gap-2 cursor-pointer px-4 py-2.5 bg-black/30 border border-zinc-700/50 rounded-xl hover:bg-zinc-800/50 transition-all">
                                    <input
                                        type="checkbox"
                                        checked={mock}
                                        onChange={(e) => setMock(e.target.checked)}
                                        className="rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/20"
                                    />
                                    <span className="text-sm text-zinc-300 font-medium">Mock</span>
                                </label>
                            </div>
                        </div>

                        <Button
                            onClick={handleRun}
                            disabled={isRunning || loading}
                            loading={loading}
                            className={`w-full relative overflow-hidden group ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {!isRunning && !loading && (
                                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            )}
                            <span className="relative flex items-center justify-center gap-2">
                                {isRunning ? (
                                    <>
                                        <Activity className="w-4 h-4 animate-pulse" />
                                        Sniper Running...
                                    </>
                                ) : (
                                    <>
                                        <Play className="w-4 h-4" />
                                        Start Sniper Agent
                                    </>
                                )}
                            </span>
                        </Button>
                    </div>
                </div>

                {/* Results Panel */}
                <div className="lg:col-span-2 bg-gradient-to-br from-zinc-900/90 to-zinc-800/90 backdrop-blur-xl p-6 rounded-2xl border border-zinc-700/50 shadow-2xl flex flex-col h-full">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="font-semibold text-white flex items-center gap-2 text-lg">
                            <div className="p-2 bg-blue-500/20 rounded-lg">
                                <Activity className="w-5 h-5 text-blue-400" />
                            </div>
                            Live Results
                        </h3>
                        {status && <StatusBadge status={status.status} />}
                    </div>

                    <div className="flex-1 bg-black/40 rounded-xl p-6 font-mono text-sm text-zinc-300 overflow-y-auto border border-zinc-800/50">
                        {!status || !status.result ? (
                            <div className="flex flex-col items-center justify-center h-full text-zinc-500">
                                <div className="relative">
                                    <div className="absolute inset-0 bg-gradient-to-br from-zinc-700 to-zinc-800 rounded-full blur-xl opacity-50"></div>
                                    <div className="relative p-6 bg-zinc-800/50 rounded-full border border-zinc-700/50">
                                        <Terminal className="w-12 h-12 opacity-50" />
                                    </div>
                                </div>
                                <p className="mt-6 text-sm font-medium">Waiting for sniper output...</p>
                                <p className="text-xs text-zinc-600 mt-2">Configure and launch the agent to begin</p>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {status.result.niche && (
                                    <div className="bg-gradient-to-br from-emerald-500/10 to-blue-500/10 p-4 rounded-xl border border-emerald-500/20">
                                        <span className="text-xs text-emerald-400 uppercase tracking-wider block mb-2 font-semibold">Active Niche</span>
                                        <div className="flex justify-between items-center">
                                            <span className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
                                                {status.result.niche}
                                            </span>
                                            {status.result.category_id && (
                                                <span className="text-xs bg-zinc-800/50 px-3 py-1.5 rounded-lg text-zinc-300 font-mono border border-zinc-700/50">
                                                    ID: {status.result.category_id}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {status.result.deals && status.result.deals.length > 0 && (
                                    <div>
                                        <div className="flex items-center justify-between mb-4">
                                            <span className="text-sm text-zinc-400 uppercase tracking-wider font-semibold">
                                                Profitable Deals ({status.result.deals.length})
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {status.result.deals.map((deal: any, i: number) => (
                                                <div
                                                    key={i}
                                                    className="group relative bg-zinc-900/50 border border-zinc-700/50 rounded-xl overflow-hidden hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-300 flex flex-col"
                                                >
                                                    {/* Image Header */}
                                                    <div className="relative h-48 bg-black/50 flex items-center justify-center overflow-hidden">
                                                        {deal.imageUrl ? (
                                                            <img 
                                                                src={deal.imageUrl} 
                                                                alt={deal.title} 
                                                                className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500"
                                                            />
                                                        ) : (
                                                            <div className="flex flex-col items-center gap-2 text-zinc-600">
                                                                <Target className="w-8 h-8 opacity-20" />
                                                                <span className="text-xs font-mono">NO IMAGE</span>
                                                            </div>
                                                        )}
                                                        
                                                        {/* Floating ROI Badge */}
                                                        {deal.analysis?.roi_percent && (
                                                            <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-md rounded-lg border border-emerald-500/30 text-emerald-400 text-xs font-bold shadow-xl">
                                                                {deal.analysis.roi_percent.toFixed(0)}% ROI
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Content Body */}
                                                    <div className="p-4 flex-1 flex flex-col justify-between">
                                                        <div>
                                                            <h4 className="font-medium text-zinc-200 leading-snug line-clamp-2 mb-3 h-10 group-hover:text-blue-400 transition-colors">
                                                                {deal.title}
                                                            </h4>
                                                            
                                                            <div className="grid grid-cols-2 gap-2 mb-4">
                                                                <div className="bg-black/30 p-2 rounded-lg border border-zinc-800/50">
                                                                    <p className="text-[10px] text-zinc-500 uppercase">Buy Now</p>
                                                                    <p className="font-mono text-zinc-300">£{deal.sellingStatus?.currentPrice?.value || deal.price}</p>
                                                                </div>
                                                                <div className="bg-black/30 p-2 rounded-lg border border-zinc-800/50">
                                                                    <p className="text-[10px] text-zinc-500 uppercase">Market Val</p>
                                                                    <p className="font-mono text-zinc-300">£{deal.analysis?.market_value || deal.ttv}</p>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <div className="flex items-center justify-between pt-3 border-t border-zinc-800/50">
                                                            <div className="flex flex-col">
                                                                <span className="text-[10px] text-zinc-500 uppercase font-medium">Net Profit</span>
                                                                <span className="text-xl font-bold text-emerald-400">+£{deal.analysis?.profit?.toFixed(2)}</span>
                                                            </div>
                                                            <a
                                                                href={deal.viewItemURL}
                                                                target="_blank"
                                                                className="px-4 py-2 bg-blue-600/10 text-blue-400 hover:bg-blue-600 hover:text-white rounded-lg text-xs font-medium transition-all flex items-center gap-2"
                                                            >
                                                                View Deal <ExternalLink className="w-3 h-3" />
                                                            </a>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {status.error && (
                                    <div className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border border-red-500/30 p-4 rounded-xl">
                                        <div className="flex items-start gap-3">
                                            <div className="p-2 bg-red-500/20 rounded-lg flex-shrink-0">
                                                <Terminal className="w-5 h-5 text-red-400" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-red-300 mb-1">Error Occurred</p>
                                                <p className="text-xs text-red-200/80">{status.error}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
