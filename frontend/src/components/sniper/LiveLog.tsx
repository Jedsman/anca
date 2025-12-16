import { useEffect, useRef } from 'react';
import { Activity, Terminal } from 'lucide-react';

interface LiveLogProps {
    logs: string[];
}

export function LiveLog({ logs }: LiveLogProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div className="bg-zinc-900/80 backdrop-blur-xl border-l border-zinc-800/50 flex flex-col h-full">
            <div className="p-4 border-b border-zinc-800/50 flex items-center justify-between">
                <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                    <Terminal className="w-3 h-3" /> Live Intelligence
                </span>
                <span className="text-[10px] text-zinc-600 font-mono">STREAMING</span>
            </div>

            <div className="flex-1 overflow-y-auto font-mono text-[10px] p-4 space-y-2">
                {logs.length === 0 ? (
                    <div className="text-zinc-600 text-center italic mt-10">System ready. Waiting for input...</div>
                ) : (
                    logs.map((line, i) => (
                         <div key={i} className="text-zinc-400 break-all border-l-2 border-zinc-800 pl-2 hover:border-zinc-600 hover:text-zinc-300 transition-colors">
                            {line}
                         </div>
                    ))
                )}
                <div ref={bottomRef} />
            </div>

            {/* Quick Stats Ticker */}
            <div className="p-4 bg-black/20 border-t border-zinc-800/50 grid grid-cols-2 gap-2">
                 <div className="bg-zinc-800/50 p-2 rounded border border-zinc-700/50">
                    <div className="text-[10px] text-zinc-500 uppercase">Latency</div>
                    <div className="text-md font-mono text-emerald-400">~120ms</div>
                 </div>
                 <div className="bg-zinc-800/50 p-2 rounded border border-zinc-700/50">
                    <div className="text-[10px] text-zinc-500 uppercase">Uptime</div>
                    <div className="text-md font-mono text-blue-400">99.9%</div>
                 </div>
            </div>
        </div>
    );
}
