import { useState, useEffect } from 'react';
import { api } from './api';
import type { SniperStatus, RateLimitStatus } from './types';
import { ControlPanel } from './components/sniper/ControlPanel';
import { DealsGrid } from './components/sniper/DealsGrid';
import { LiveLog } from './components/sniper/LiveLog';

export default function App() {
  // State
  const [status, setStatus] = useState<SniperStatus | null>(null);
  const [rateLimit, setRateLimit] = useState<RateLimitStatus | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Inputs
  const [query, setQuery] = useState('');
  const [minProfit, setMinProfit] = useState(10.0);
  const [mode, setMode] = useState<'discover' | 'niche' | 'search'>('discover');
  const [mock, setMock] = useState(false);

  // Poll for data
  useEffect(() => {
    const fetchData = async () => {
        try {
            const [statusRes, rateRes, logsRes] = await Promise.all([
                api.getSniperStatus(),
                api.getRateLimitStatus(),
                api.getLogs()
            ]);
            setStatus(statusRes.data);
            setRateLimit(rateRes.data);
            setLogs(logsRes.data.logs || []);
        } catch (e) {
            console.error("Polling error", e);
        }
    };

    fetchData(); // Initial
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    try {
        await api.runSniper({
            query: query || undefined,
            min_profit: minProfit,
            auto: mode === 'niche',
            discover: mode === 'discover',
            mock: mock
        });
    } catch (err: any) {
        alert("Failed to start sniper: " + err.message);
    } finally {
        setLoading(false);
    }
  };

  const isRunning = status?.status === 'running';

  return (
    <div className="flex h-screen w-screen bg-black text-white font-sans overflow-hidden selection:bg-emerald-500/30">
        
        {/* Left: Control Panel (20% - Fixed 320px) */}
        <div className="w-[320px] h-full flex-shrink-0 relative z-20">
            <ControlPanel 
                isRunning={isRunning}
                loading={loading}
                onStart={handleStart}
                mode={mode} setMode={setMode}
                query={query} setQuery={setQuery}
                minProfit={minProfit} setMinProfit={setMinProfit}
                mock={mock} setMock={setMock}
                rateLimit={rateLimit}
            />
        </div>

        {/* Center: Mission Grid (Flexible) */}
        <div className="flex-1 h-full relative z-10 bg-zinc-950">
             {/* Background Effects */}
             <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900 via-zinc-950 to-black opacity-50 pointer-events-none" />
             
             <div className="h-full overflow-y-auto p-8 relative">
                <DealsGrid 
                    deals={status?.result?.deals || []} 
                    niche={status?.result?.niche}
                />
             </div>
        </div>

        {/* Right: Live Log (20% - Fixed 300px) */}
        <div className="w-[300px] h-full flex-shrink-0 relative z-20">
            {/* Pass reversed logs if we want newest at bottom? API usually returns linear list */}
            <LiveLog logs={logs} />
        </div>
    </div>
  );
}
