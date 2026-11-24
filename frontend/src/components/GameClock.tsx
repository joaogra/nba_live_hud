import { formatNbaClock, formatPeriod } from "../utils/clockParser";

interface GameClockProps {
  period: number;
  clock: string;
}

export function GameClock({ period, clock }: GameClockProps) {
  return (
    <div className="flex flex-col items-center justify-center border-x border-slate-800 bg-slate-900/90 px-4 py-2 min-w-[92px]">
      <span className="text-[11px] font-bold uppercase tracking-widest text-amber-400">
        {formatPeriod(period)}
      </span>
      <span className="text-lg font-mono font-bold tabular-nums text-white">
        {formatNbaClock(clock)}
      </span>
    </div>
  );
}