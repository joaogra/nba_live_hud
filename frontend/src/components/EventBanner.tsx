import {
  Activity,
  AlertTriangle,
  ArrowLeftRight,
  Flame,
  ShieldAlert,
  Trophy,
} from "lucide-react";
import { GameEvent } from "../types/game";
import { EVENT_STYLES, getTeamColors } from "../config/theme";

interface EventBannerProps {
  event: GameEvent | null;
  queueSize: number;
}

function getEventIcon(actionType: string) {
  switch (actionType) {
    case "3pt":
      return <Flame className="h-4 w-4" />;
    case "2pt":
    case "freethrow":
      return <Trophy className="h-4 w-4" />;
    case "foul":
      return <AlertTriangle className="h-4 w-4" />;
    case "substitution":
      return <ArrowLeftRight className="h-4 w-4" />;
    case "block":
    case "steal":
      return <ShieldAlert className="h-4 w-4" />;
    default:
      return <Activity className="h-4 w-4" />;
  }
}

export function EventBanner({ event, queueSize }: EventBannerProps) {
  if (!event) return null;

  const style = EVENT_STYLES[event.action_type] ?? {
    label: event.action_type.toUpperCase(),
    accentClass: "border-slate-500",
    badgeBgClass: "bg-slate-700 text-white",
  };
  const teamColors = getTeamColors(event.team);

  return (
    <div
      key={event.action_number}
      className={`animate-event-in flex items-center justify-between gap-4 rounded-xl border-l-4 ${style.accentClass} border border-slate-800/90 bg-slate-950/92 px-4 py-3 shadow-2xl backdrop-blur-md max-w-md`}
    >
      <div className="flex flex-col gap-1">
        {/* Cabeçalho do alerta: Badge do tipo + Sigla do time */}
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider ${style.badgeBgClass}`}
          >
            {getEventIcon(event.action_type)}
            {style.label}
          </span>

          <span
            className="rounded px-1.5 py-0.5 text-[11px] font-bold text-white"
            style={{ backgroundColor: teamColors.primary }}
          >
            {event.team}
          </span>
        </div>

        {/* Descrição oficial do lance */}
        <p className="text-sm font-semibold text-slate-100 leading-snug">
          {event.description}
        </p>
      </div>

      {/* Indicador discreto caso existam mais eventos aguardando na fila */}
      {queueSize > 1 && (
        <span className="shrink-0 rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-slate-300">
          +{queueSize - 1}
        </span>
      )}
    </div>
  );
}