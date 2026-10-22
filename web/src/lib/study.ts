// Build-time access to the study data. Reads the report and the gzipped replays from
// ../experiments, resolved from process.cwd() because bundled modules run from dist/.
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { gunzipSync } from 'node:zlib';
import type { AttackInfo, CardInfo, Game, Replay } from './types';

const EXPERIMENTS = resolve(process.cwd(), '..', 'experiments');

type Breakdown = { wins: number; total_games: number; win_rate: number; wilson_ci_95: [number, number] };
export type Checkpoint = {
  checkpoint_path: string;
  weights_sha256: string;
  provenance: {
    variant: string;
    seed: number;
    training_steps: number;
    training_deck_families: string[];
    total_samples: number;
    train_samples: number;
    val_samples: number;
    initial_val_acc: number;
    final_val_acc: number;
    training_duration_seconds: number;
  };
  total_games: number;
  total_points: number;
  overall_win_rate: number;
  overall_wilson_ci_95: [number, number];
  family_breakdown: Record<string, Breakdown>;
  opponent_breakdown: Record<string, Breakdown>;
};
type VariantSummary = {
  pooled_points: number;
  pooled_games: number;
  pooled_win_rate: number;
  pooled_wilson_ci_95: [number, number];
};
export type Report = {
  completed_at: string;
  hypothesis: string;
  environment: { card_catalog_sha256: string; attack_catalog_sha256: string };
  study_configuration: {
    training_seeds: number[];
    training_deck_families: string[];
    heldout_test_deck_families: string[];
    eval_opponents: string[];
    eval_seeds: number[];
    eval_seed_role: string;
  };
  ablation_results: {
    summary_by_variant: Record<string, VariantSummary>;
    win_rate_delta_diverse_vs_fixed: number;
    delta_confidence_interval_95: [number, number];
  };
  checkpoint_evaluations: Record<string, Checkpoint[]>;
  games: Game[];
};

let report: Report | null = null;
export function getReport(): Report {
  report ??= JSON.parse(readFileSync(join(EXPERIMENTS, 'ml-experiment-report.json'), 'utf8')) as Report;
  return report;
}

/** The 360 games in a fixed canonical order: variant, seed, deck, opponent, label, pair, game. */
export function getGames(): Game[] {
  const order = (g: Game) => [
    g.variant === 'fixed-opponent-pool' ? 0 : 1,
    g.training_seed,
    g.family === 'psychic-mewtwo' ? 0 : 1,
    ['heuristic', 'first', 'random'].indexOf(g.opponent),
    g.eval_seed,
    g.pair_index,
    g.game_in_pair,
  ];
  return [...getReport().games].sort((a, b) => {
    const x = order(a), y = order(b);
    for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return (x[i] ?? 0) - (y[i] ?? 0);
    return 0;
  });
}

const replays = new Map<string, Replay>();
export function getReplay(id: string): Replay {
  const hit = replays.get(id);
  if (hit) return hit;
  const raw = gunzipSync(readFileSync(join(EXPERIMENTS, 'replays', `${id}.json.gz`)));
  const replay = JSON.parse(raw.toString('utf8')) as Replay;
  replays.set(id, replay);
  return replay;
}

export type CastCard = CardInfo & { id: number; moves: { name: string; damage: number; uses: number }[] };

/** Every card the held-out decks used, with how often each attack was used across all 360 games. */
export function getCast(): CastCard[] {
  const cards = new Map<number, CardInfo>();
  const uses = new Map<string, number>();
  const attacks = new Map<number, AttackInfo>();
  for (const g of getGames()) {
    const r = getReplay(g.game_id);
    for (const [id, c] of Object.entries(r.cards)) cards.set(Number(id), c);
    for (const [id, a] of Object.entries(r.attacks)) attacks.set(Number(id), a);
    for (const f of r.frames) for (const e of f.events) {
      if (e.type !== 'Attack' || e.card === undefined || e.attack === undefined) continue;
      const k = `${e.card}:${e.attack}`;
      uses.set(k, (uses.get(k) ?? 0) + 1);
    }
  }
  return [...cards].map(([id, c]) => ({
    ...c,
    id,
    moves: [...uses].filter(([k]) => k.startsWith(`${id}:`)).map(([k, n]) => {
      const a = attacks.get(Number(k.split(':')[1]))!;
      return { name: a.name, damage: a.damage, uses: n };
    }).sort((a, b) => b.uses - a.uses),
  }));
}

export function getCheckpoints(): Checkpoint[] {
  const ev = getReport().checkpoint_evaluations;
  return [...(ev['fixed-opponent-pool'] ?? []), ...(ev['diverse-opponent-pool'] ?? [])];
}
