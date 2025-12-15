import { twMerge } from 'tailwind-merge';
import { Loader2 } from 'lucide-react';
import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline';
    loading?: boolean;
}

export function Button({ children, className, variant = 'primary', loading, ...props }: ButtonProps) {
    const base = "flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed";
    const variants = {
        primary: "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20",
        secondary: "bg-zinc-800 hover:bg-zinc-700 text-zinc-300",
        outline: "border border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-white"
    };

    return (
        <button className={twMerge(base, variants[variant], className)} disabled={loading || props.disabled} {...props}>
             {loading && <Loader2 className="w-4 h-4 animate-spin" />}
             {children}
        </button>
    );
}
