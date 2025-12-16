export interface Deal {
    title: string;
    viewItemURL: string;
    imageUrl?: string;
    price: number; // Fallback
    sellingStatus?: {
        currentPrice?: {
            value: number;
        };
        bidCount?: number;
        timeLeft?: string;
    };
    listingInfo?: {
        watchCount?: number;
    };
    condition?: {
        conditionDisplayName?: string;
    };
    ttv: number; // Fallback
    analysis?: {
        profit: number;
        roi_percent: number;
        market_value: number;
        cost_basis: number;
    };
}

export interface SniperResult {
    niche: string;
    category_id?: string;
    deals: Deal[];
    pending_queries: string[];
}

export interface SniperStatus {
    status: 'idle' | 'running' | 'completed' | 'failed';
    result?: SniperResult;
    error?: string;
    logs: string[];
}

export interface RateLimitStatus {
    calls_today: number;
    max_calls_per_day: number;
    remaining_calls: number;
    reset_time: string;
}
