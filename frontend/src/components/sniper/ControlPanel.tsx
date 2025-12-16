import { Play, Sparkles, Activity, Search, Box } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';

interface ControlPanelProps {
    isRunning: boolean;
    loading: boolean;
    onStart: () => void;
    mode: 'discover' | 'niche' | 'search';
    setMode: (m: 'discover' | 'niche' | 'search') => void;
    query: string;
    setQuery: (q: string) => void;
    minProfit: number;
    setMinProfit: (n: number) => void;
    mock: boolean;
    setMock: (b: boolean) => void;
    rateLimit: any;
}

export function ControlPanel({
    isRunning, loading, onStart,
    mode, setMode, query, setQuery, minProfit, setMinProfit, mock, setMock, rateLimit
}: ControlPanelProps) {
    
    return (
        <div className="bg-zinc-900/80 backdrop-blur-xl border-r border-zinc-800/50 flex flex-col h-full">
            {/* Header */}
            <div className="p-6 border-b border-zinc-800/50">
                <div className="flex items-center gap-3 mb-1">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-blue-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent tracking-tight">
                        ANCA
                    </h1>
                </div>
                <p className="text-[10px] text-zinc-500 font-mono pl-11 uppercase tracking-widest">Mission Control</p>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-8">
                {/* 1. Status Section */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between text-xs text-zinc-400 uppercase tracking-wider font-semibold">
                        <span>System Status</span>
                        {isRunning ? (
                            <span className="text-emerald-400 flex items-center gap-1.5 animate-pulse">
                                <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Active
                            </span>
                        ) : (
                            <span className="text-zinc-500 flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full bg-zinc-600"></span> Idle
                            </span>
                        )}
                    </div>

                    <Button 
                        onClick={onStart}
                        disabled={isRunning || loading}
                        className={`w-full py-6 text-sm font-bold tracking-wide uppercase transition-all duration-300 relative overflow-hidden group ${
                            isRunning 
                                ? 'bg-zinc-800 text-zinc-400 border-zinc-700 cursor-not-allowed' 
                                : 'bg-white text-black hover:bg-emerald-400 hover:text-black hover:shadow-[0_0_20px_rgba(52,211,153,0.3)]'
                        }`}
                    >
                        {isRunning ? (
                            <span className="flex items-center justify-center gap-2">
                                <Activity className="w-4 h-4 animate-spin" /> Scanning...
                            </span>
                        ) : (
                            <span className="flex items-center justify-center gap-2 group-hover:scale-105 transition-transform">
                                <Play className="w-4 h-4 fill-current" /> Initialize Scan
                            </span>
                        )}
                    </Button>
                </div>

                {/* 2. Mode Config */}
                <div className="space-y-4">
                    <span className="text-xs text-zinc-500 uppercase tracking-wider font-semibold block">Operation Mode</span>
                    <div className="grid grid-cols-1 gap-2">
                        <button 
                            onClick={() => setMode('discover')}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all text-left ${
                                mode === 'discover' 
                                    ? 'bg-blue-500/10 border-blue-500/50 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.1)]' 
                                    : 'bg-zinc-800/30 border-transparent text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300'
                            }`}
                        >
                            <Sparkles className="w-4 h-4" />
                            <div>
                                <div className="text-xs font-bold uppercase">Discovery</div>
                                <div className="text-[10px] opacity-70">Auto-find niches</div>
                            </div>
                        </button>
                        
                        <button 
                            onClick={() => setMode('niche')}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all text-left ${
                                mode === 'niche' 
                                    ? 'bg-purple-500/10 border-purple-500/50 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.1)]' 
                                    : 'bg-zinc-800/30 border-transparent text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300'
                            }`}
                        >
                            <Box className="w-4 h-4" />
                            <div>
                                <div className="text-xs font-bold uppercase">Niche Target</div>
                                <div className="text-[10px] opacity-70">Specific category</div>
                            </div>
                        </button>

                        <button 
                            onClick={() => setMode('search')}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all text-left ${
                                mode === 'search' 
                                    ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)]' 
                                    : 'bg-zinc-800/30 border-transparent text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300'
                            }`}
                        >
                            <Search className="w-4 h-4" />
                            <div>
                                <div className="text-xs font-bold uppercase">Keyword Search</div>
                                <div className="text-[10px] opacity-70">Direct lookup</div>
                            </div>
                        </button>
                    </div>

                    {mode !== 'discover' && (
                        <div className="pt-2">
                             <Input 
                                value={query}
                                onChange={(e: any) => setQuery(e.target.value)}
                                placeholder={mode === 'niche' ? "Enter Niche..." : "Enter Keywords..."}
                                className="bg-black/50 border-zinc-700"
                            />
                        </div>
                    )}
                </div>

                {/* 3. Parameters */}
                <div className="space-y-4 pt-4 border-t border-zinc-800/50">
                     <span className="text-xs text-zinc-500 uppercase tracking-wider font-semibold block">Parameters</span>
                     <div className="flex items-center justify-between bg-black/30 p-3 rounded-lg border border-zinc-800/50">
                        <span className="text-xs text-zinc-400">Min Profit (£)</span>
                        <input 
                            type="number"
                            value={minProfit}
                            onChange={(e) => setMinProfit(parseFloat(e.target.value))}
                            className="w-16 bg-transparent text-right text-sm font-mono text-white outline-none focus:border-b border-zinc-600"
                        />
                     </div>
                     
                     <label className="flex items-center justify-between cursor-pointer group">
                        <span className="text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors">Mock Mode</span>
                        <div className={`w-10 h-5 rounded-full relative transition-colors ${mock ? 'bg-emerald-500' : 'bg-zinc-700'}`}>
                            <input type="checkbox" checked={mock} onChange={(e) => setMock(e.target.checked)} className="hidden" />
                            <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-transform ${mock ? 'left-6' : 'left-1'}`} />
                        </div>
                     </label>
                </div>
            </div>

            {/* Footer: API Stats */}
            <div className="p-4 bg-black/20 border-t border-zinc-800/50">
                 {rateLimit && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-[10px] text-zinc-500 uppercase tracking-wide">
                            <span>API Usage</span>
                            <span>{rateLimit.calls_today} / {rateLimit.max_calls_per_day}</span>
                        </div>
                        <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                            <div 
                                className={`h-full transition-all duration-500 ${rateLimit.calls_today > 4000 ? 'bg-red-500' : 'bg-blue-500'}`}
                                style={{ width: `${(rateLimit.calls_today / rateLimit.max_calls_per_day) * 100}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
