from asyncio import events
import asyncio
import json
from pathlib import Path
from typing import Optional
import httpx

from app.models import GameEvent
from app.state import GameStateManager

class NbaPoller:
    """Worker assíncrono que ingere lances da CDN da NBA"""

    def __init__(self, state_manager: GameStateManager, interval_seconds: float = 3.0, replay_file: Optional[str] = None,):
        self.state = state_manager
        self.interval = interval_seconds
        self.replay_file = replay_file
        self.last_action_number = 0
        self._etag: Optional[str] = None

    def _normalize_action(self, raw: dict) -> GameEvent:
        """Converte o dicionário da NBA na classe do projeto (GameEvent)"""
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

    async def run(self):
        """Ponto de entrada da tarefa em Background"""
        if self.replay_file:
            await self._run_replay_loop()
        else:
            await self._run_live_loop()

    async def _fetch_game_metadata(self, client: httpx.AsyncClient):
            """Busca uma única vez os metadados completos da partida via boxscore."""
            url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{self.state.game_id}.json"
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nba.com/"}

            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    game = resp.json().get("game", {})
                    home = game.get("homeTeam", {})
                    away = game.get("awayTeam", {})
                    arena = game.get("arena", {})

                    home_tricode = home.get("teamTricode")
                    away_tricode = away.get("teamTricode")

                    if home_tricode and away_tricode:
                        await self.state.set_metadata(
                            home_team=home_tricode,
                            away_team=away_tricode,
                            home_team_name=home.get("teamName", ""),
                            away_team_name=away.get("teamName", ""),
                            home_record=f"{home.get('wins', 0)}-{home.get('losses', 0)}",
                            away_record=f"{away.get('wins', 0)}-{away.get('losses', 0)}",
                            arena_name=arena.get("arenaName", ""),
                            arena_city=arena.get("arenaCity", ""),
                        )
                        print(
                            f"[Metadata] {away_tricode} @ {home_tricode} | "
                            f"{arena.get('arenaName', 'Arena desconhecida')}"
                        )
            except httpx.RequestError as exc:
                print(f"[Metadata Error] Falha ao buscar boxscore: {exc}")

    async def _run_replay_loop(self):
        """Função de teste offline: Lê um JSON local e roda 1 ação por intervalo"""
        file_path = Path(self.replay_file)
        if not file_path.exists():
            print(f"[Replay Error] Arquivo não encontrado: {file_path}")
            return
        
        with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
        actions = data.get("game", {}).get("actions", [])

        teams = list({a["teamTricode"] for a in actions if a.get("teamTricode")})
        if len(teams) >= 2:
            await self.state.set_metadata(home_team=teams[0], away_team=teams[1])

        print (f"[Replay] Iniciando simulação com {len(actions)} lances (intervalo: {self.interval}s)...")

        for raw_action in actions:
            event = self._normalize_action(raw_action)
            self.last_action_number = event.action_number

            print(f"[Replay #{event.action_number}] {event.team} - {event.description}")
            await self.state.process_and_broadcast(event)
            await asyncio.sleep(self.interval)
        
        print("[Replay] Simulação concluida")

    async def _run_live_loop(self):
        """Consulta a CDN da NBA continuamente e processa apenas lances novos"""

        url = f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{self.state.game_id}.json"
        base_headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nba.com/",
        }
    
        print(f"[Live Poller] Monitorando jogo {self.state.game_id} a cada {self.interval}s...")

        async with httpx.AsyncClient(timeout=5.0) as client:

            await self._fetch_game_metadata(client)

            while True:
                headers = dict(base_headers)
                if self._etag:
                    headers["If-None-Match"] = self._etag

                try:
                    resp = await client.get(url, headers=headers)

                    if resp.status_code == 304:
                        await asyncio.sleep(self.interval)
                        continue

                    if resp.status_code == 200:
                        self._etag = resp.headers.get("ETag")
                        actions = resp.json().get("game", {}).get("actions", [])

                        new_actions = [
                            a for a in actions if a["actionNumber"] > self.last_action_number
                        ]

                        for raw_action in new_actions:
                            event = self._normalize_action(raw_action)
                            self.last_action_number = event.action_number
                            await self.state.process_and_broadcast(event)
                    
                    elif resp.status_code == 429:
                        print("[Live Poller] Rate limit(429). Aguardando 10s...")
                        await asyncio.sleep(10)
                        continue
                
                except httpx.RequestError as exc:
                    print (f"[Live Poller] Erro de rede: {exc}")

                await asyncio.sleep(self.interval)
                
