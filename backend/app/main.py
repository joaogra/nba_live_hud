import asyncio 
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.state import GameStateManager
from app.poller import NbaPoller

#Modo Replay
#GAME_ID = "0022600123"
#REPLAY_MODE_FILE = "mocks/sample_game.json"

#Modo ao vivo
GAME_ID = "0022600243"
REPLAY_MODE_FILE = None

state_manager = GameStateManager(GAME_ID, home_team = "LAL", away_team="BOS")
poller = NbaPoller(
    state_manager = state_manager,
    interval_seconds=2.5,
    replay_file=REPLAY_MODE_FILE
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    poller_task = asyncio.create_task(poller.run())
    yield
    poller_task.cancel()

app = FastAPI(title="NBA LIVE HUD Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "running",
        "game_id": state_manager.game_id,
        "score": f"{state_manager.home_team} {state_manager.score_home} X {state_manager.away_team} {state_manager.score_away}",
        "connected_clients": len(state_manager.active_connections),
    }

@app.websocket("/ws/game")
async def game_websocket_endpoint(websocket: WebSocket):
        await state_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
            
        except WebSocketDisconnect:
            state_manager.disconnect(websocket)