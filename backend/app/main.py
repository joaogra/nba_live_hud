import argparse
import asyncio
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.state import GameStateManager
from app.poller import NbaPoller

DEFAULT_REPLAY_GAME_ID = "0022600123"
DEFAULT_REPLAY_FILE = "mocks/sample_game.json"

env_game_id = os.getenv("GAME_ID", "").strip()

if env_game_id:
    GAME_ID = env_game_id
    REPLAY_MODE_FILE = None
else:
    GAME_ID = DEFAULT_REPLAY_GAME_ID
    REPLAY_MODE_FILE = DEFAULT_REPLAY_FILE

state_manager = GameStateManager(GAME_ID, home_team="LAL", away_team="BOS")
poller = NbaPoller(
    state_manager=state_manager,
    interval_seconds=2.5,
    replay_file=REPLAY_MODE_FILE,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mode_label = (
        f"AO VIVO (GAME_ID={GAME_ID})"
        if not REPLAY_MODE_FILE
        else f"REPLAY ({REPLAY_MODE_FILE})"
    )
    print(f"[Server] Iniciando NBA Live HUD em modo: {mode_label}")
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
        "mode": "replay" if REPLAY_MODE_FILE else "live",
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inicia o servidor backend do NBA Live HUD."
    )
    parser.add_argument(
        "game_id",
        nargs="?",
        default=None,
        help="ID da partida da NBA para monitorar ao vivo (ex: 0022600244). Se omitido, roda o modo Replay local.",
    )
    parser.add_argument(
        "--game-id",
        dest="flag_game_id",
        default=None,
        help="ID da partida da NBA para monitorar ao vivo (alternativa via flag).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host do servidor (padrão: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta do servidor (padrão: 8000).",
    )
    args = parser.parse_args()

    selected_game_id = args.flag_game_id or args.game_id
    if selected_game_id:
        os.environ["GAME_ID"] = selected_game_id.strip()
    else:
        os.environ.pop("GAME_ID", None)

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=True)
