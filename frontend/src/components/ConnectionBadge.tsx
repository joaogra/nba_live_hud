interface ConnectionBadgeProps {
  isConnected: boolean;
}

export function ConnectionBadge({ isConnected }: ConnectionBadgeProps) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-slate-950/85 px-3 py-1 text-xs font-semibold tracking-wider text-slate-200 border border-slate-800 shadow-lg backdrop-blur-md">
      <span
        className={`h-2 w-2 rounded-full ${
          isConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
        }`}
      />
      <span>{isConnected ? "WS LIVE" : "RECONECTANDO..."}</span>
    </div>
  );
}