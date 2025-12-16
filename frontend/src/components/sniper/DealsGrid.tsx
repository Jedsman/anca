import { ExternalLink, TrendingUp, DollarSign, Target } from 'lucide-react';
import type { Deal } from '../../types';

interface DealsGridProps {
    deals: Deal[];
    niche?: string;
}

export function DealsGrid({ deals, niche }: DealsGridProps) {
    if (!deals || deals.length === 0) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-zinc-600">
                <div className="w-24 h-24 rounded-full bg-zinc-900/50 border border-zinc-800 flex items-center justify-center mb-6">
                    <Target className="w-10 h-10 opacity-20" />
                </div>
                <h3 className="text-lg font-medium text-zinc-500 mb-2">Target Acquisition Mode</h3>
                <p className="text-sm max-w-xs text-center opacity-60">Initiate scan to populate the kill list.</p>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            {niche && (
                <div className="mb-6 flex items-center gap-3">
                    <div className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-xs font-bold text-emerald-400 uppercase tracking-wide animate-fadeIn">
                        Target Acquired
                    </div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">{niche}</h2>
                    <span className="text-sm text-zinc-500 font-mono">({deals.length} items)</span>
                </div>
            )}

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-10">
                {deals.map((deal, i) => (
                    <div 
                        key={i}
                        className="group relative bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-emerald-500/50 hover:shadow-[0_0_30px_rgba(16,185,129,0.1)] transition-all duration-300 flex flex-col"
                    >
                        {/* Image Header */}
                        <div className="relative h-48 bg-black">
                            {deal.imageUrl ? (
                                <img 
                                    src={deal.imageUrl} 
                                    alt={deal.title} 
                                    className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700"
                                />
                            ) : (
                                <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
                                    <Target className="w-12 h-12 text-zinc-800" />
                                </div>
                            )}
                            
                            {/* Overlay Gradient */}
                            <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 via-transparent to-transparent opacity-90" />

                            {/* Bids Badge */}
                            <div className="absolute top-3 left-3 px-2 py-1 bg-black/60 backdrop-blur rounded text-white text-[10px] font-bold uppercase border border-zinc-700">
                                {deal.sellingStatus?.bidCount || 0} Bids
                            </div>

                            {/* Floating ROI Badge */}
                            {deal.analysis?.roi_percent && (
                                <div className="absolute top-3 right-3 px-2 py-1 bg-black/80 backdrop-blur border border-emerald-500/50 rounded text-emerald-400 text-xs font-bold font-mono shadow-xl">
                                    {deal.analysis.roi_percent.toFixed(0)}% ROI
                                </div>
                            )}

                             {/* Price Tag */}
                             <div className="absolute bottom-3 left-3 bg-white/10 backdrop-blur px-2 py-1 rounded text-white text-xs font-bold font-mono">
                                £{deal.sellingStatus?.currentPrice?.value || deal.price}
                             </div>
                        </div>

                        {/* Content */}
                        <div className="p-4 flex-1 flex flex-col justify-between relative bg-zinc-900">
                             <div>
                                <h3 className="font-medium text-zinc-200 leading-snug line-clamp-2 h-10 mb-4 group-hover:text-blue-400 transition-colors">
                                    {deal.title}
                                </h3>

                                <div className="grid grid-cols-2 gap-3 mb-4">
                                     <div className="bg-black/40 p-2 rounded border border-zinc-800">
                                        <div className="text-[10px] text-zinc-500 uppercase mb-0.5">Est. Value</div>
                                        <div className="text-sm font-mono text-zinc-300">£{deal.analysis?.market_value || deal.ttv}</div>
                                     </div>
                                     <div className="bg-emerald-900/10 p-2 rounded border border-emerald-500/20">
                                        <div className="text-[10px] text-emerald-500/70 uppercase mb-0.5">Net Profit</div>
                                        <div className="text-sm font-bold font-mono text-emerald-400">+£{deal.analysis?.profit?.toFixed(2)}</div>
                                     </div>
                                </div>
                             </div>

                             <a 
                                href={deal.viewItemURL}
                                target="_blank"
                                className="w-full py-2 bg-zinc-800 hover:bg-blue-600 hover:text-white text-zinc-400 text-xs font-bold uppercase rounded transition-colors flex items-center justify-center gap-2"
                             >
                                Inspect on eBay <ExternalLink className="w-3 h-3" />
                             </a>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
