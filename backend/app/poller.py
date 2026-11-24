import asyncio
import json
from pathlib import Path
import re
import time
from typing import Optional
import httpx

from app.models import GameEvent
from app.state import GameStateManager

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
)


class NbaPoller:
    """Worker assíncrono que ingere lances ao vivo da NBA."""

    def __init__(
        self,
        state_manager: GameStateManager,
        interval_seconds: float = 3.0,
        replay_file: Optional[str] = None,
    ):
        self.state = state_manager
        self.interval = interval_seconds
        self.replay_file = replay_file
        self.last_action_number = 0
        self._seen_actions: set[int] = set()
        self._etag: Optional[str] = None
        self._metadata_loaded = False
        self._next_build_id: Optional[str] = None

    def _normalize_action(self, raw: dict) -> GameEvent:
        """Converte o dicionário da NBA na classe do projeto (GameEvent)."""
        return GameEvent(
            action_number=raw["actionNumber"],
            action_type=raw.get("actionType", "unknown"),
            sub_type=raw.get("subType") or "",
            team=raw.get("teamTricode") or "SYS",
            player=raw.get("playerNameI") or "",
            description=raw.get("description") or "",
            score_home=int(raw.get("scoreHome") or 0),
            score_away=int(raw.get("scoreAway") or 0),
            period=int(raw.get("period") or 1),
            clock=raw.get("clock") or "PT12M00.00S",
        )

    def _extract_on_court(self, team_data: dict) -> list[str]:
        """Extrai os 5 jogadores atualmente em quadra (ou titulares) no formato 'N. Sobrenome'."""
        players = team_data.get("players", [])
        on_court = [
            p.get("nameI") for p in players if p.get("oncourt") == "1" and p.get("nameI")
        ]
        if len(on_court) == 5:
            return on_court

        return [
            p.get("nameI") for p in players if p.get("starter") == "1" and p.get("nameI")
        ][:5]

    async def run(self):
        """Ponto de entrada da tarefa em Background."""
        if self.replay_file:
            await self._run_replay_loop()
        else:
            await self._run_live_loop()

    async def _fetch_live_payload(self, client: httpx.AsyncClient) -> Optional[dict]:
        """
        Busca os dados ao vivo (boxscore + playByPlay) da partida.
        Usa a rota JSON do Next.js da NBA (ou extrai o __NEXT_DATA__ da página do jogo)
        pois o acesso direto à cdn.nba.com/static/json/liveData retorna 403 no WAF/Akamai.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        }
        cache_buster = int(time.time() * 1000)

        if self._next_build_id:
            json_url = (
                f"https://www.nba.com/_next/data/{self._next_build_id}"
                f"/en/game/{self.state.game_id}/play-by-play.json?_t={cache_buster}"
            )
            resp = await client.get(
                json_url,
                headers={**headers, "Accept": "application/json"},
                follow_redirects=True,
            )
            if resp.status_code == 200:
                return resp.json().get("pageProps", {})
            # Se o buildId mudou, limpa para redescobrir via HTML
            self._next_build_id = None

        page_url = f"https://www.nba.com/game/{self.state.game_id}/play-by-play?_t={cache_buster}"
        resp = await client.get(page_url, headers=headers, follow_redirects=True)
        if resp.status_code != 200:
            print(f"[Live Poller] Status HTTP inesperado ({resp.status_code}) para {page_url}")
            return None

        match = NEXT_DATA_RE.search(resp.text)
        if not match:
            print("[Live Poller] __NEXT_DATA__ não encontrado na página da NBA.")
            return None

        next_data = json.loads(match.group(1))
        self._next_build_id = next_data.get("buildId")
        return next_data.get("props", {}).get("pageProps", {})

    async def _apply_game_metadata(self, game: dict):
        """Extrai e atualiza metadados e quintetos em quadra a partir do objeto game."""
        home = game.get("homeTeam", {})
        away = game.get("awayTeam", {})
        arena = game.get("arena", {})

        home_tricode = home.get("teamTricode")
        away_tricode = away.get("teamTricode")

        if not (home_tricode and away_tricode):
            return

        home_wins = home.get("teamWins", home.get("wins", 0))
        home_losses = home.get("teamLosses", home.get("losses", 0))
        away_wins = away.get("teamWins", away.get("wins", 0))
        away_losses = away.get("teamLosses", away.get("losses", 0))

        home_on_court = self._extract_on_court(home)
        away_on_court = self._extract_on_court(away)

        if not self._metadata_loaded:
            await self.state.set_metadata(
                home_team=home_tricode,
                away_team=away_tricode,
                home_team_name=home.get("teamName", ""),
                away_team_name=away.get("teamName", ""),
                home_record=f"{home_wins}-{home_losses}",
                away_record=f"{away_wins}-{away_losses}",
                arena_name=arena.get("arenaName", ""),
                arena_city=arena.get("arenaCity", ""),
                home_on_court=home_on_court,
                away_on_court=away_on_court,
            )
            self._metadata_loaded = True
            print(
                f"[Metadata] {away_tricode} @ {home_tricode} | "
                f"{arena.get('arenaName', 'Arena desconhecida')}"
            )
        else:
            if home_on_court:
                self.state.home_on_court = home_on_court
            if away_on_court:
                self.state.away_on_court = away_on_court

    async def _run_replay_loop(self):
        """Função de teste offline: Lê um JSON local e roda 1 ação por intervalo."""
        file_path = Path(self.replay_file)
        if not file_path.exists():
            print(f"[Replay Error] Arquivo não encontrado: {file_path}")
            return

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        game_data = data.get("game", {})
        actions = game_data.get("actions", [])

        if game_data.get("homeTeam") and game_data.get("awayTeam"):
            await self.state.set_metadata(
                home_team=game_data["homeTeam"],
                away_team=game_data["awayTeam"],
                home_team_name=game_data.get("homeTeamName", ""),
                away_team_name=game_data.get("awayTeamName", ""),
                home_record=game_data.get("homeRecord", ""),
                away_record=game_data.get("awayRecord", ""),
                arena_name=game_data.get("arenaName", ""),
                arena_city=game_data.get("arenaCity", ""),
                home_on_court=game_data.get("homeOnCourt", []),
                away_on_court=game_data.get("awayOnCourt", []),
            )

        print(
            f"[Replay] Iniciando simulação com {len(actions)} lances (intervalo: {self.interval}s)..."
        )

        for raw_action in actions:
            event = self._normalize_action(raw_action)
            self.last_action_number = event.action_number

            print(f"[Replay #{event.action_number}] {event.team} - {event.description}")
            await self.state.process_and_broadcast(event)
            await asyncio.sleep(self.interval)

        print("[Replay] Simulação concluída.")

    async def _run_live_loop(self):
        """Consulta os dados ao vivo da NBA continuamente e processa apenas lances novos."""
        is_first_fetch = True
        print(f"[Live Poller] Monitorando jogo {self.state.game_id} a cada {self.interval}s...")

        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                try:
                    page_props = await self._fetch_live_payload(client)
                    if page_props:
                        game = page_props.get("game", {})
                        if game:
                            await self._apply_game_metadata(game)

                        actions = page_props.get("playByPlay", {}).get("actions", [])

                        if is_first_fetch and actions:
                            # Registra todos os lances já ocorridos para não reenviar
                            for raw_action in actions:
                                self._seen_actions.add(raw_action["actionNumber"])

                            # Sincroniza placar, relógio e os 5 últimos lances sem disparar enxurrada de banners
                            self.state.recent_actions.clear()
                            for raw_action in actions[-5:]:
                                event = self._normalize_action(raw_action)
                                event.home_on_court = list(self.state.home_on_court)
                                event.away_on_court = list(self.state.away_on_court)
                                self.state.recent_actions.append(event)

                            latest = self._normalize_action(actions[-1])
                            self.state.score_home = latest.score_home
                            self.state.score_away = latest.score_away
                            self.state.period = latest.period
                            self.state.clock = latest.clock
                            self.last_action_number = max(self._seen_actions)
                            is_first_fetch = False

                            print(
                                f"[Live Sync] Placar sincronizado: "
                                f"{self.state.away_team} {self.state.score_away} x "
                                f"{self.state.score_home} {self.state.home_team} "
                                f"(Q{self.state.period} {self.state.clock}) - "
                                f"Último lance #{self.last_action_number}"
                            )

                            if self.state.active_connections:
                                await self.state._broadcast_raw(
                                    self.state.get_snapshot().model_dump_json()
                                )
                        else:
                            new_actions = [
                                a for a in actions if a["actionNumber"] not in self._seen_actions
                            ]
                            for raw_action in new_actions:
                                self._seen_actions.add(raw_action["actionNumber"])
                                event = self._normalize_action(raw_action)
                                self.last_action_number = max(
                                    self.last_action_number, event.action_number
                                )
                                print(
                                    f"[Live #{event.action_number}] {event.team} - {event.description}"
                                )
                                await self.state.process_and_broadcast(event)

                except httpx.RequestError as exc:
                    print(f"[Live Poller] Erro de rede: {exc}")
                except Exception as exc:
                    print(f"[Live Poller] Erro ao processar dados: {exc}")

                await asyncio.sleep(self.interval)