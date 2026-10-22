// Plain-language names for study factors. Shared by the server pages and the replay viewer.
import type { EndReason, Family, Game, Opponent, Result, Variant } from './types';

export const variantName: Record<Variant, string> = {
  'fixed-opponent-pool': 'Trained vs 1 opponent',
  'diverse-opponent-pool': 'Trained vs 3 opponents',
};
export const variantShort: Record<Variant, string> = {
  'fixed-opponent-pool': 'One-opponent',
  'diverse-opponent-pool': 'Three-opponent',
};
export const familyName: Record<Family, string> = {
  'psychic-mewtwo': 'Mewtwo deck',
  'colorless-snorlax': 'Snorlax deck',
};
export const opponentName: Record<Opponent, string> = {
  heuristic: 'Rule-based bot',
  first: 'First-choice bot',
  random: 'Random bot',
};
export const opponentShort: Record<Opponent, string> = {
  heuristic: 'Rule-based',
  first: 'First-choice',
  random: 'Random',
};
export const endingName: Record<EndReason, string> = {
  prizes: 'All Prize cards taken',
  'deck-out': 'A deck ran out',
  'no-pokemon': 'No Pokémon left in play',
  invalid: 'Invalid action',
  unknown: 'Unknown ending',
};
export const endingShort: Record<EndReason, string> = {
  prizes: 'Prize cards',
  'deck-out': 'deck ran out',
  'no-pokemon': 'no Pokémon left',
  invalid: 'invalid action',
  unknown: 'unknown',
};
export const resultVerb: Record<Result, string> = { win: 'won', loss: 'lost', draw: 'drew' };

/** Each training style was run from three seeds; readers see them as runs 1 to 3. */
export const runOf = (seed: number) => [11, 29, 47].indexOf(seed) + 1;
export const checkpointName = (g: Pick<Game, 'variant' | 'training_seed'>) =>
  `${variantShort[g.variant]} AI\u00A0#${runOf(g.training_seed)}`;
export const seatName = (seat: number) => (seat === 0 ? 'first' : 'second');

/** One readable sentence about how a game ended, from the AI's side. */
export function outcomeSentence(g: Game): string {
  const t = g.turns;
  if (g.result === 'draw') return `The game was a draw on turn ${t}.`;
  const won = g.result === 'win';
  switch (g.end_reason) {
    case 'prizes':
      return won ? `The AI won by taking all its Prize cards on turn ${t}.`
        : `The AI lost on turn ${t}: the opponent took all its Prize cards.`;
    case 'deck-out':
      return won ? `The AI won on turn ${t}: the opponent’s deck ran out.`
        : `The AI lost on turn ${t}: its deck ran out.`;
    case 'no-pokemon':
      return won ? `The AI won on turn ${t}: the opponent had no Pokémon left in play.`
        : `The AI lost on turn ${t}: it had no Pokémon left in play.`;
    default:
      return `The AI ${resultVerb[g.result]} on turn ${t} (${endingShort[g.end_reason]}).`;
  }
}

export const pct = (x: number, digits = 1) => `${(x * 100).toFixed(digits)}%`;
/** Signed number with a true minus sign (U+2212), for differences. */
export const signed = (x: number, digits = 1) => `${x < 0 ? '−' : '+'}${Math.abs(x).toFixed(digits)}`;
