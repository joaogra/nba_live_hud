from pydantic import BaseModel
from typing import Literal, Optional


class GameEvent(BaseModel):
    """Representa um lance individual normalizado que ocorreu na partida."""
    event_type: Literal["GAME_ACTION"] = "GAME_ACTION"
    action_number: int
    action_type: str
    sub_type: Optional[str] = ""
    team: str
    player: str
    description: str
    score_home: int
    score_away: int
    period: int
    clock: str
    home_on_court: list[str] = []
    away_on_court: list[str] = []


class GameSnapshot(BaseModel):
    """Representa o estado consolidado e os metadados da partida para novos clientes."""
    event_type: Literal["STATE_SNAPSHOT"] = "STATE_SNAPSHOT"
    game_id: str
    home_team: str
    home_team_name: str = ""
    home_record: str = ""  
    away_team: str
    away_team_name: str = ""
    away_record: str = ""     
    arena_name: str = ""       
    arena_city: str = ""      
    score_home: int
    score_away: int
    period: int
    clock: str
    home_on_court: list[str] = []
    away_on_court: list[str] = []
    recent_actions: list[GameEvent] = []