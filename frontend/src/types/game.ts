export interface GameEvent {
  event_type: "GAME_ACTION";
  action_number: number;
  action_type: string;
  sub_type: string;
  team: string;
  player: string;
  description: string;
  score_home: number;
  score_away: number;
  period: number;
  clock: string;
  home_on_court: string[];
  away_on_court: string[];
}

export interface GameSnapshot {
  event_type: "STATE_SNAPSHOT";
  game_id: string;
  home_team: string;
  home_team_name: string;
  home_record: string;
  away_team: string;
  away_team_name: string;
  away_record: string;
  arena_name: string;
  arena_city: string;
  score_home: number;
  score_away: number;
  period: number;
  clock: string;
  home_on_court: string[];
  away_on_court: string[];
  recent_actions: GameEvent[];
}

export type ServerMessage = GameSnapshot | GameEvent;