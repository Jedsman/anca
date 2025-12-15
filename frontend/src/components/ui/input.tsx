import { twMerge } from 'tailwind-merge';
import { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
}

export function Input({ label, className, ...props }: InputProps) {
    return (
        <div className="flex flex-col gap-1.5">
            {label && <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">{label}</label>}
            <input 
                className={twMerge("bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors", className)}
                {...props}
            />
        </div>
    );
}
