import { GameUIState } from "../hooks/useGameSocket";
import { TeamBlock } from "./TeamBlock";
import { GameClock } from "./GameClock";

interface ScoreboardProps {
  gameState: GameUIState;
}

export function Scoreboard({ gameState }: ScoreboardProps) {
  const hasArenaInfo = Boolean(gameState.arenaName);

  return (
    <div className="inline-flex flex-col overflow-hidden rounded-xl border border-slate-800/90 bg-slate-950/92 shadow-2xl backdrop-blur-md">
      {/* Linha principal do placar: Visitante | Relógio | Mandante */}
      <div className="flex items-stretch">
        <TeamBlock
          tricode={gameState.awayTeam}
          teamName={gameState.awayTeamName}
          record={gameState.awayRecord}
          score={gameState.scoreAway}
          align="left"
        />

        <GameClock period={gameState.period} clock={gameState.clock} />

        <TeamBlock
          tricode={gameState.homeTeam}
          teamName={gameState.homeTeamName}
          record={gameState.homeRecord}
          score={gameState.scoreHome}
          align="right"
        />
      </div>

      {/* Barra inferior opcional com Arena e Cidade */}
      {hasArenaInfo && (
        <div className="border-t border-slate-800/80 bg-slate-900/60 px-4 py-1 text-center text-[11px] font-medium tracking-wide text-slate-400">
          {gameState.arenaName}
          {gameState.arenaCity ? ` • ${gameState.arenaCity}` : ""}
        </div>
      )}
    </div>
  );
}