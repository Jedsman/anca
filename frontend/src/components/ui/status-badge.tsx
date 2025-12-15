import clsx from 'clsx';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { ReactNode } from 'react';

export function StatusBadge({ status }: { status: string }) {
    const styles: Record<string, string> = {
        pending: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
        running: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        completed: "bg-green-500/10 text-green-500 border-green-500/20",
        failed: "bg-red-500/10 text-red-500 border-red-500/20"
    };
    const icon: Record<string, ReactNode> = {
        pending: <Loader2 className="w-3 h-3 animate-spin"/>,
        running: <Loader2 className="w-3 h-3 animate-spin"/>,
        completed: <CheckCircle2 className="w-3 h-3"/>,
        failed: <AlertCircle className="w-3 h-3"/>
    };

    return (
        <span className={clsx("flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border", styles[status] || styles.pending)}>
            {icon[status]}
            {status.toUpperCase()}
        </span>
    );
}
