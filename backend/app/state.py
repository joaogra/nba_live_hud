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

        if self.active_connections:
            await self._broadcast_raw(self.get_snapshot().model_dump_json())

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
            recent_actions=list(self.recent_actions),
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
        self.recent_actions.append(event)

        if self.active_connections:
            await self._broadcast_raw(event.model_dump_json())