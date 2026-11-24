import { useGameSocket } from "./hooks/useGameSocket";
import { Scoreboard } from "./components/Scoreboard";
import { EventBanner } from "./components/EventBanner";
import { ConnectionBadge } from "./components/ConnectionBadge";
import { OnCourtRoster } from "./components/OnCourtRoster";
import { formatNbaClock, formatPeriod } from "./utils/clockParser";

const WS_URL = "ws://127.0.0.1:8000/ws/game";

export function App() {
  const { gameState, activeEvent, queueSize, isConnected } =
    useGameSocket(WS_URL);

  return (
    <main className="relative min-h-screen w-screen select-none p-6 flex flex-col items-center justify-center gap-6">
      {/* Indicador de conexão no canto superior direito */}
      <div className="fixed top-5 right-6">
        <ConnectionBadge isConnected={isConnected} />
      </div>

      {/* Placar Central Principal */}
      <section className="flex flex-col items-center">
        <Scoreboard gameState={gameState} />
      </section>

      {/* Área Central: Quinteto Visitante | Banner de Lances + Feed | Quinteto Mandante */}
      <section className="flex flex-wrap items-start justify-center gap-6 w-full max-w-5xl">
        <OnCourtRoster
          tricode={gameState.awayTeam}
          teamName={gameState.awayTeamName}
          players={gameState.awayOnCourt}
          activeEvent={activeEvent}
          align="left"
        />

        {/* Coluna Central: Alerta Animado + Últimos Lances */}
        <div className="flex flex-col items-center gap-4 min-w-[340px] max-w-md flex-1">
          <div className="min-h-[84px] flex items-center justify-center w-full">
            {activeEvent ? (
              <EventBanner event={activeEvent} queueSize={queueSize} />
            ) : (
              <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/50 px-5 py-4 text-center text-xs font-medium text-slate-500 w-full">
                Aguardando próximo lance da partida...
              </div>
            )}
          </div>

          {/* Mini-feed dos últimos lances */}
          {gameState.recentActions.length > 0 && (
            <div className="w-full rounded-2xl border border-slate-800/80 bg-slate-950/85 p-4 shadow-xl backdrop-blur-md">
              <h4 className="text-[11px] font-extrabold uppercase tracking-widest text-slate-400 mb-2.5">
                Últimos Lances
              </h4>
              <ul className="flex flex-col gap-2">
                {gameState.recentActions.map((action) => (
                  <li
                    key={action.action_number}
                    className="flex items-center justify-between gap-3 rounded-lg bg-slate-900/70 px-3 py-2 text-xs border border-slate-800/60"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="font-bold text-amber-400 shrink-0">
                        {action.team}
                      </span>
                      <span className="text-slate-200 truncate">
                        {action.description}
                      </span>
                    </div>
                    <span className="font-mono text-[11px] text-slate-400 shrink-0">
                      {formatPeriod(action.period)} {formatNbaClock(action.clock)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <OnCourtRoster
          tricode={gameState.homeTeam}
          teamName={gameState.homeTeamName}
          players={gameState.homeOnCourt}
          activeEvent={activeEvent}
          align="right"
        />
      </section>
    </main>
  );
}

export default App;