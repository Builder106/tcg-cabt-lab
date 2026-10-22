// The table's sorts: each one groups the same 360 games into piles.
import { checkpointName, endingName, familyName, opponentName, runOf, variantName } from './labels';
import type { EndReason, Family, Game, Opponent, Variant } from './types';

export type SortKey =
  | 'training' | 'deck' | 'training-and-deck' | 'opponent' | 'seat' | 'ending' | 'checkpoint' | 'matchup';

export type Pile = {
  key: string;
  label: string;
  /** Short label for dense layouts (the matchup grid). */
  short: string;
  games: Game[];
  wins: number;
  draws: number;
  losses: number;
  points: number;
  rate: number;
  ci: [number, number];
};

export type Sort = {
  key: SortKey;
  /** Words that finish "Sort the 360 games by ..." */
  by: string;
  path: string;
  piles: Pile[];
  /** Columns of cards per pile on wide screens and on phones. */
  cols: { wide: number; phone: number };
};

/** Wilson score interval at 95%, on points (a draw counts half), as in the study report. */
export function wilson(points: number, n: number, z = 1.959964): [number, number] {
  if (n === 0) return [0, 0];
  const p = points / n;
  const d = 1 + (z * z) / n;
  const c = (p + (z * z) / (2 * n)) / d;
  const h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [c - h, c + h];
}

const resultRank = { win: 0, draw: 1, loss: 2 } as const;

export function makePile(key: string, label: string, short: string, games: Game[]): Pile {
  const ordered = [...games].sort((a, b) => resultRank[a.result] - resultRank[b.result]);
  const wins = games.filter((g) => g.result === 'win').length;
  const draws = games.filter((g) => g.result === 'draw').length;
  const points = wins + draws / 2;
  return {
    key, label, short, games: ordered, wins, draws, losses: games.length - wins - draws, points,
    rate: games.length ? points / games.length : 0, ci: wilson(points, games.length),
  };
}

function groupBy<K extends string | number>(games: Game[], keys: K[], f: (g: Game) => K) {
  return keys.map((k) => [k, games.filter((g) => f(g) === k)] as const);
}

const VARIANTS: Variant[] = ['fixed-opponent-pool', 'diverse-opponent-pool'];
const FAMILIES: Family[] = ['psychic-mewtwo', 'colorless-snorlax'];
const OPPONENTS: Opponent[] = ['heuristic', 'first', 'random'];
const ENDINGS: EndReason[] = ['prizes', 'deck-out', 'no-pokemon'];
const SEEDS = [11, 29, 47];

export const SORT_ORDER: SortKey[] = [
  'training', 'deck', 'training-and-deck', 'opponent', 'seat', 'ending', 'checkpoint', 'matchup',
];

export const sortPath = (key: SortKey) => (key === 'training' ? '/' : `/sort/${key}/`);

export function buildSort(key: SortKey, games: Game[]): Sort {
  const base = { key, path: sortPath(key) };
  switch (key) {
    case 'training':
      return { ...base, by: 'training opponents', cols: { wide: 30, phone: 12 },
        piles: groupBy(games, VARIANTS, (g) => g.variant).map(([k, gs]) => makePile(k, variantName[k], variantName[k], gs)) };
    case 'deck':
      return { ...base, by: 'deck', cols: { wide: 30, phone: 12 },
        piles: groupBy(games, FAMILIES, (g) => g.family).map(([k, gs]) => makePile(k, familyName[k], familyName[k], gs)) };
    case 'training-and-deck':
      return { ...base, by: 'training and deck', cols: { wide: 15, phone: 10 },
        piles: FAMILIES.flatMap((f) => VARIANTS.map((v) => makePile(
          `${v}:${f}`, `${variantName[v]}, ${familyName[f]}`, `${variantName[v]}, ${familyName[f]}`,
          games.filter((g) => g.variant === v && g.family === f)))) };
    case 'opponent':
      return { ...base, by: 'opponent', cols: { wide: 20, phone: 12 },
        piles: groupBy(games, OPPONENTS, (g) => g.opponent).map(([k, gs]) => makePile(k, opponentName[k], opponentName[k], gs)) };
    case 'seat':
      return { ...base, by: 'seat', cols: { wide: 30, phone: 12 },
        piles: groupBy(games, [0, 1], (g) => g.policy_seat).map(([k, gs]) => makePile(
          `seat-${k}`, k === 0 ? 'AI in the first seat' : 'AI in the second seat', k === 0 ? 'First seat' : 'Second seat', gs)) };
    case 'ending':
      return { ...base, by: 'how the game ended', cols: { wide: 20, phone: 12 },
        piles: groupBy(games, ENDINGS, (g) => g.end_reason).map(([k, gs]) => makePile(k, endingName[k], endingName[k], gs)) };
    case 'checkpoint':
      return { ...base, by: 'which AI played', cols: { wide: 10, phone: 10 },
        piles: VARIANTS.flatMap((v) => SEEDS.map((s) => makePile(
          `${v}:${s}`, checkpointName({ variant: v, training_seed: s }), `AI #${runOf(s)}`,
          games.filter((g) => g.variant === v && g.training_seed === s)))) };
    case 'matchup':
      return { ...base, by: 'AI and matchup', cols: { wide: 5, phone: 5 },
        piles: VARIANTS.flatMap((v) => SEEDS.flatMap((s) => FAMILIES.flatMap((f) => OPPONENTS.map((o) => makePile(
          `${v}:${s}:${f}:${o}`, `${checkpointName({ variant: v, training_seed: s })}, ${familyName[f]}, ${opponentName[o]}`,
          `${o}`, games.filter((g) => g.variant === v && g.training_seed === s && g.family === f && g.opponent === o)))))) };
  }
}
