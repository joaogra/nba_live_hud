import { UserCheck } from "lucide-react";
import { getTeamColors } from "../config/theme";
import { GameEvent } from "../types/game";

interface OnCourtRosterProps {
  tricode: string;
  teamName: string;
  players: string[];
  activeEvent: GameEvent | null;
  align: "left" | "right";
}

export function OnCourtRoster({
  tricode,
  teamName,
  players,
  activeEvent,
  align,
}: OnCourtRosterProps) {
  const colors = getTeamColors(tricode);
  const isRight = align === "right";

  return (
    <div className="flex flex-col rounded-2xl border border-slate-800/90 bg-slate-950/90 p-4 shadow-2xl backdrop-blur-md w-60">
      {/* Cabeçalho do Quinteto */}
      <div
        className={`flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3 ${
          isRight ? "flex-row-reverse text-right" : "flex-row text-left"
        }`}
      >
        <div>
          <span className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
            Em Quadra
          </span>
          <h3 className="text-sm font-bold text-white">
            {teamName || tricode}
          </h3>
        </div>
        <span
          className="h-3 w-3 rounded-full"
          style={{ backgroundColor: colors.primary }}
        />
      </div>

      {/* Lista dos 5 jogadores */}
      <ul className="flex flex-col gap-2">
        {players.length === 0 ? (
          <li className="text-xs text-slate-500 italic py-2 text-center">
            Aguardando escalação...
          </li>
        ) : (
          players.map((player) => {
            const isHighlighted =
              activeEvent?.team === tricode && activeEvent?.player === player;
            const justSubbedIn =
              isHighlighted &&
              activeEvent?.action_type === "substitution" &&
              activeEvent?.sub_type.toLowerCase() === "in";

            return (
              <li
                key={player}
                className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm font-semibold transition-all duration-300 ${
                  justSubbedIn
                    ? "bg-indigo-500/20 border border-indigo-400/60 text-indigo-200 animate-event-in"
                    : isHighlighted
                    ? "bg-amber-500/15 border border-amber-400/50 text-amber-200"
                    : "bg-slate-900/75 border border-slate-800/80 text-slate-200"
                }`}
              >
                <span className="truncate">{player}</span>
                {justSubbedIn ? (
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-300 bg-indigo-500/30 px-1.5 py-0.5 rounded">
                    ENTROU
                  </span>
                ) : (
                  <UserCheck className="h-3.5 w-3.5 text-emerald-400/70 shrink-0" />
                )}
              </li>
            );
          })
        )}
      </ul>
    </div>
  );
}