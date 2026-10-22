// Data contract from src/tcg_cabt_lab/showcase.py (replay schema version 1).

export type Variant = 'fixed-opponent-pool' | 'diverse-opponent-pool';
export type Family = 'psychic-mewtwo' | 'colorless-snorlax';
export type Opponent = 'heuristic' | 'first' | 'random';
export type Result = 'win' | 'loss' | 'draw';
export type EndReason = 'prizes' | 'deck-out' | 'no-pokemon' | 'invalid' | 'unknown';

export type Game = {
  game_id: string;
  variant: Variant;
  training_seed: number;
  weights_sha256: string;
  family: Family;
  opponent: Opponent;
  eval_seed: number;
  pair_index: number;
  game_in_pair: number;
  policy_seat: 0 | 1;
  result: Result;
  end_reason: EndReason;
  engine_reason_code: number | null;
  turns: number;
  decisions: number;
  prizes_taken: { policy: number; opponent: number };
  steps: number;
  duration_seconds: number;
  statuses: string[];
};

export type CardInfo = { name: string; hp: number; card_type: number; energy_type: number; ex: boolean };
export type AttackInfo = { name: string; damage: number; text: string };

export type Pokemon = {
  id: number;
  hp: number;
  max_hp: number;
  energy: number[];
  tools: number[];
  evolved_from: number[];
};

export type Player = {
  active: Pokemon[];
  bench: Pokemon[];
  hand: number[];
  hand_count: number;
  deck_count: number;
  discard: number[];
  prizes: number[];
  status: string[];
};

export type GameEvent = {
  type: string;
  player?: number;
  card?: number;
  target?: number;
  active?: number;
  bench?: number;
  attack?: number;
  value?: number;
  heads?: boolean;
  recovered?: boolean;
  has_basic?: boolean;
  result?: number;
  reason?: number;
  from?: string;
  to?: string;
};

export type Frame = {
  turn: number;
  actor: number;
  prompt: string;
  min: number;
  max: number;
  options: string[];
  chosen: number[];
  scores: number[] | null;
  events: GameEvent[];
  stadium: number[];
  players: [Player, Player];
};

export type Replay = {
  schema_version: number;
  game: Game;
  cards: Record<string, CardInfo>;
  attacks: Record<string, AttackInfo>;
  frames: Frame[];
};

export type View = 'agent' | 'spectator';
