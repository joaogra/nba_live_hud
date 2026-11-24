import asyncio
from collections import deque
from fastapi import WebSocket
from app.models import GameEvent, GameSnapshot


class GameStateManager:
    def __init__(self, game_id: str, home_team: str = "HOME", away_team: str = "AWAY"):
        self.game_id = game_id
        self.home_team = home_team
        self.home_team_name = ""
        self.home_record = ""
        self.away_team = away_team
        self.away_team_name = ""
        self.away_record = ""
        self.arena_name = ""
        self.arena_city = ""

        self.score_home = 0
        self.score_away = 0
        self.period = 1
        self.clock = "PT12M00.00S"

        self.home_on_court: list[str] = []
        self.away_on_court: list[str] = []

        self.recent_actions: deque[GameEvent] = deque(maxlen=5)
        self.active_connections: set[WebSocket] = set()

    async def set_metadata(
        self,
        home_team: str,
        away_team: str,
        home_team_name: str = "",
        away_team_name: str = "",
        home_record: str = "",
        away_record: str = "",
        arena_name: str = "",
        arena_city: str = "",
        home_on_court: list[str] | None = None,
        away_on_court: list[str] | None = None,
    ):
        """Atualiza os metadados do jogo e notifica clientes já conectados."""
        self.home_team = home_team
        self.away_team = away_team
        self.home_team_name = home_team_name
        self.away_team_name = away_team_name
        self.home_record = home_record
        self.away_record = away_record
        self.arena_name = arena_name
        self.arena_city = arena_city

        if home_on_court is not None:
            self.home_on_court = home_on_court
        if away_on_court is not None:
            self.away_on_court = away_on_court

        if self.active_connections:
            await self._broadcast_raw(self.get_snapshot().model_dump_json())

    def _update_on_court(self, event: GameEvent):
        """Atualiza a lista de 5 jogadores em quadra quando ocorre substituição."""
        if event.action_type != "substitution" or not event.player:
            return

        roster = (
            self.home_on_court
            if event.team == self.home_team
            else self.away_on_court
        )

        sub_type = (event.sub_type or "").lower()
        if sub_type == "out" and event.player in roster:
            roster.remove(event.player)
        elif sub_type == "in" and event.player not in roster:
            roster.append(event.player)

    def get_snapshot(self) -> GameSnapshot:
        return GameSnapshot(
            game_id=self.game_id,
            home_team=self.home_team,
            home_team_name=self.home_team_name,
            home_record=self.home_record,
            away_team=self.away_team,
            away_team_name=self.away_team_name,
            away_record=self.away_record,
            arena_name=self.arena_name,
            arena_city=self.arena_city,
            score_home=self.score_home,
            score_away=self.score_away,
            period=self.period,
            clock=self.clock,
            home_on_court=list(self.home_on_court),
            away_on_court=list(self.away_on_court),
            recent_actions=list(reversed(self.recent_actions)),
        )

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        await websocket.send_text(self.get_snapshot().model_dump_json())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def _broadcast_raw(self, payload: str):
        connections_snapshot = list(self.active_connections)
        results = await asyncio.gather(
            *(ws.send_text(payload) for ws in connections_snapshot),
            return_exceptions=True,
        )
        for ws, result in zip(connections_snapshot, results):
            if isinstance(result, Exception):
                self.disconnect(ws)

    async def process_and_broadcast(self, event: GameEvent):
            self.score_home = event.score_home
            self.score_away = event.score_away
            self.period = event.period
            self.clock = event.clock

            self._update_on_court(event)
            event.home_on_court = list(self.home_on_court)
            event.away_on_court = list(self.away_on_court)

            self.recent_actions.append(event)

            if self.active_connections:
                await self._broadcast_raw(event.model_dump_json())