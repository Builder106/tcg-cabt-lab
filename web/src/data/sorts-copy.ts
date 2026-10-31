// Each sort is a Trainer card. In the hand it shows its name and one rules line; played on the
// table it carries the finding. Numbers come from the piles; fixed facts from site.ts.
import { facts } from './site';
import { pct } from '@/lib/labels';
import type { Pile, Sort, SortKey } from '@/lib/sorts';

export type SortCopy = {
  /** Card name, in the hand and on the played card. */
  name: string;
  /** One rules line on the card in the hand. */
  rule: string;
  /** Page title (SEO). */
  title: string;
  headline: string;
  lede: string;
  notes: string[];
  description: string;
};

const p = (piles: Pile[], key: string) => piles.find((x) => x.key === key)!;

/** Name and rules line for every sort, for the hand (no pile numbers needed). */
export const cardText: Record<SortKey, { name: string; rule: string }> = {
  training: { name: 'Training', rule: 'Two piles: AIs trained against one opponent or three.' },
  deck: { name: 'Deck', rule: 'One pile per deck. Both players use the same deck.' },
  'training-and-deck': { name: 'Training and deck', rule: 'Four piles: each training style on each deck.' },
  opponent: { name: 'Opponent', rule: 'A rule-based bot, a first-choice bot or a random one.' },
  seat: { name: 'Seat', rule: 'Which of the two seats the AI sat in.' },
  ending: { name: 'Ending', rule: 'Prize cards, an empty deck, or no Pokémon left.' },
  checkpoint: { name: 'Training run', rule: 'Six AIs: each training style, three times.' },
  matchup: { name: 'Matchup grid', rule: 'Every AI against every deck and opponent.' },
};

export function sortCopy(sort: Sort, delta: number, deltaCi: [number, number]): SortCopy {
  const P = sort.piles;
  const copy: Record<SortKey, () => Omit<SortCopy, 'name' | 'rule'>> = {
    training: () => {
      const f = p(P, 'fixed-opponent-pool'), d = p(P, 'diverse-opponent-pool');
      return {
        title: 'A dead heat',
        headline: 'A dead heat.',
        lede: `Games won (a draw counts half): one opponent ${pct(f.rate)}, three opponents ${pct(d.rate)}.`,
        notes: [
          'A tiny AI learned the Pokémon card game by copying a bot. Half the copies trained against one kind of opponent, half against three.',
          `Over 180 games each, a ${Math.abs(delta * 100).toFixed(1)}% difference is noise. Luck alone could have left the three-opponent AIs ${Math.abs(deltaCi[0] * 100).toFixed(1)}% behind or ${(deltaCi[1] * 100).toFixed(1)}% ahead, so the extra variety didn’t measurably help.`,
        ],
        description: `The same tiny Pokémon card game AI, trained two ways, scored ${pct(f.rate)} and ${pct(d.rate)} over 180 games each, with decks it had never seen. Sort all 360 games yourself.`,
      };
    },
    deck: () => {
      const m = p(P, 'psychic-mewtwo'), s = p(P, 'colorless-snorlax');
      return {
        title: 'Sorted by deck',
        headline: 'The deck mattered more.',
        lede: `Games won with the Mewtwo deck ${pct(m.rate)}, with the Snorlax deck ${pct(s.rate)}.`,
        notes: [
          `That ${((s.rate - m.rate) * 100).toFixed(1)}% gap between decks (180 games each) is far bigger than the ${Math.abs(delta * 100).toFixed(1)}% gap between training styles.`,
          'In every game both players used the same deck, and no AI saw either deck during training.',
        ],
        description: `With the Mewtwo deck the AI scored ${pct(m.rate)}; with the Snorlax deck, ${pct(s.rate)}. The deck made a bigger difference than how it was trained.`,
      };
    },
    'training-and-deck': () => {
      const mf = p(P, 'fixed-opponent-pool:psychic-mewtwo'), md = p(P, 'diverse-opponent-pool:psychic-mewtwo');
      const sf = p(P, 'fixed-opponent-pool:colorless-snorlax'), sd = p(P, 'diverse-opponent-pool:colorless-snorlax');
      return {
        title: 'Sorted by training and deck',
        headline: 'Each style won one deck.',
        lede: `Games won. Mewtwo: ${pct(md.rate)} (3 opponents), ${pct(mf.rate)} (1). Snorlax: ${pct(sf.rate)} (1), ${pct(sd.rate)} (3).`,
        notes: [
          'Each pile holds only 90 games, so luck alone could shift each number by about 10% either way. Still, the two decks point opposite ways and cancel out, so one overall average hides both.',
        ],
        description: 'Split by deck, AIs trained against three opponents did better with Mewtwo, and AIs trained against one did better with Snorlax. One average hides both.',
      };
    },
    opponent: () => {
      const h = p(P, 'heuristic'), f = p(P, 'first'), r = p(P, 'random');
      return {
        title: 'Sorted by opponent',
        headline: 'Hardest against its teacher.',
        lede: `Games won against the rule-based bot ${pct(h.rate)}, the first-choice bot ${pct(f.rate)}, the random bot ${pct(r.rate)}.`,
        notes: [
          'Every AI learned by copying the rule-based bot, so here it plays its own teacher. The first-choice bot always takes the first option on offer.',
          'Each opponent played 120 games: 60 per deck, half with the seats swapped.',
        ],
        description: `Against the rule-based bot it learned from, the AI scored ${pct(h.rate)}. Against simpler bots it scored more.`,
      };
    },
    seat: () => {
      const a = p(P, 'seat-0'), b = p(P, 'seat-1');
      return {
        title: 'Sorted by seat',
        headline: 'The seat barely mattered.',
        lede: `Games won from the first seat ${pct(a.rate)}, from the second seat ${pct(b.rate)}.`,
        notes: [
          `A ${Math.abs((b.rate - a.rate) * 100).toFixed(1)}% gap over 180 games a seat is well within luck. Every game was played twice with the seats swapped, so neither seat gets an edge; the cards are shuffled fresh each time.`,
        ],
        description: `In the first seat the AI scored ${pct(a.rate)}; in the second, ${pct(b.rate)}.`,
      };
    },
    ending: () => {
      const z = p(P, 'prizes'), d = p(P, 'deck-out'), n = p(P, 'no-pokemon');
      return {
        title: 'Sorted by how the game ended',
        headline: 'Few games reached the last Prize.',
        lede: `Of 360 games: ${z.games.length} by Prize cards, ${d.games.length} by an empty deck, ${n.games.length} with no Pokémon left.`,
        notes: [
          'Mewtwo games mostly ended with a deck running out (117 of 180), Snorlax games with a player out of Pokémon (163 of 180).',
          `Team Rocket’s Mewtwo ex needs four Team Rocket’s Pokémon in play to attack. It attacked ${facts.mewtwoAttacks} times in 180 games; Eevee ex never did.`,
        ],
        description: `${z.games.length} games ended with every Prize card taken, ${d.games.length} when a deck ran out and ${n.games.length} when a player had no Pokémon left in play.`,
      };
    },
    checkpoint: () => {
      const rates = P.map((x) => x.rate);
      return {
        title: 'Sorted by training run',
        headline: 'Same recipe, very different AIs.',
        lede: `Games won by each of the six AIs: from ${pct(Math.min(...rates))} to ${pct(Math.max(...rates))}.`,
        notes: [
          'Each AI played 60 games, so luck alone could shift each one by about 12%. Still, retraining the same way moved scores more than the training style did.',
          `Training stopped at ${facts.usedSteps.toLocaleString('en-US')} of ${facts.plannedSteps.toLocaleString('en-US')} planned steps. ${facts.copyAccuracy}`,
        ],
        description: 'Each training style was run three times, and each AI played 60 games. The spread between runs is wider than the gap between styles.',
      };
    },
    matchup: () => ({
      title: 'The full matchup grid',
      headline: 'Every matchup, ten games each.',
      lede: 'Rows: the six AIs. Columns: deck and opponent. Each cell scores 10 games: a win is 1 point, a draw ½.',
      notes: [
        'Each cell holds five pairs of games, with the seats swapped within each pair. Open any card to replay it.',
      ],
      description: 'Six AIs, two decks and three opponents. Each cell holds ten games you can open and replay.',
    }),
  };
  return { ...cardText[sort.key], ...copy[sort.key]() };
}
