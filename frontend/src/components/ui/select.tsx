import { twMerge } from 'tailwind-merge';
import { SelectHTMLAttributes } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    options: { value: string; label: string }[];
}

export function Select({ label, options, className, ...props }: SelectProps) {
     return (
        <div className="flex flex-col gap-1.5">
            {label && <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">{label}</label>}
            <select 
                className={twMerge("bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-zinc-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors appearance-none", className)}
                {...props}
            >
                {options.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
        </div>
    );
}
