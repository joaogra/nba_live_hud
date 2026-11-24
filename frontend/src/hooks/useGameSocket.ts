import { useEffect, useRef, useState } from "react";
import { GameEvent, ServerMessage } from "../types/game";

export interface GameUIState {
  homeTeam: string;
  homeTeamName: string;
  homeRecord: string;
  awayTeam: string;
  awayTeamName: string;
  awayRecord: string;
  arenaName: string;
  arenaCity: string;
  scoreHome: number;
  scoreAway: number;
  period: number;
  clock: string;
  homeOnCourt: string[];
  awayOnCourt: string[];
  recentActions: GameEvent[];
}

const INITIAL_STATE: GameUIState = {
  homeTeam: "HOME",
  homeTeamName: "",
  homeRecord: "",
  awayTeam: "AWAY",
  awayTeamName: "",
  awayRecord: "",
  arenaName: "",
  arenaCity: "",
  scoreHome: 0,
  scoreAway: 0,
  period: 1,
  clock: "PT12M00.00S",
  homeOnCourt: [],
  awayOnCourt: [],
  recentActions: [],
};

const HIGHLIGHT_TYPES = new Set([
  "2pt",
  "3pt",
  "freethrow",
  "foul",
  "substitution",
  "turnover",
  "block",
  "steal",
]);

export function useGameSocket(wsUrl: string) {
  const [gameState, setGameState] = useState<GameUIState>(INITIAL_STATE);
  const [eventQueue, setEventQueue] = useState<GameEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    let isMounted = true;

    function connect() {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        if (!isMounted) return;
        setIsConnected(true);
      };

      socket.onmessage = (messageEvent) => {
        if (!isMounted) return;
        const data: ServerMessage = JSON.parse(messageEvent.data);

        if (data.event_type === "STATE_SNAPSHOT") {
          setGameState({
            homeTeam: data.home_team,
            homeTeamName: data.home_team_name,
            homeRecord: data.home_record,
            awayTeam: data.away_team,
            awayTeamName: data.away_team_name,
            awayRecord: data.away_record,
            arenaName: data.arena_name,
            arenaCity: data.arena_city,
            scoreHome: data.score_home,
            scoreAway: data.score_away,
            period: data.period,
            clock: data.clock,
            homeOnCourt: data.home_on_court ?? [],
            awayOnCourt: data.away_on_court ?? [],
            recentActions: data.recent_actions ?? [],
          });
        } else if (data.event_type === "GAME_ACTION") {
          setGameState((prev) => ({
            ...prev,
            scoreHome: data.score_home,
            scoreAway: data.score_away,
            period: data.period,
            clock: data.clock,
            homeOnCourt:
              data.home_on_court.length > 0 ? data.home_on_court : prev.homeOnCourt,
            awayOnCourt:
              data.away_on_court.length > 0 ? data.away_on_court : prev.awayOnCourt,
            recentActions: [data, ...prev.recentActions].slice(0, 5),
          }));

          const isMissedShot =
            (data.action_type === "2pt" ||
              data.action_type === "3pt" ||
              data.action_type === "freethrow") &&
            data.description.toUpperCase().startsWith("MISS");

          if (HIGHLIGHT_TYPES.has(data.action_type) && !isMissedShot) {
            setEventQueue((prev) => [...prev, data]);
          }
        }
      };

      socket.onclose = () => {
        if (!isMounted) return;
        setIsConnected(false);
        reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
      };

      socket.onerror = () => socket.close();
    }

    // Pequeno atraso inicial evita que o ciclo duplo do React StrictMode
    // abra e feche um WebSocket descartável gerando falso erro no console.
    const initialTimer = window.setTimeout(connect, 50);

    return () => {
      isMounted = false;
      clearTimeout(initialTimer);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);

      const ws = wsRef.current;
      if (ws) {
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        ws.onopen = null;
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        } else if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => ws.close();
        }
      }
    };
  }, [wsUrl]);

  useEffect(() => {
    if (eventQueue.length === 0) return;

    const timer = window.setTimeout(() => {
      setEventQueue((prev) => prev.slice(1));
    }, 3500);

    return () => clearTimeout(timer);
  }, [eventQueue]);

  return {
    gameState,
    activeEvent: eventQueue[0] || null,
    queueSize: eventQueue.length,
    isConnected,
  };
}